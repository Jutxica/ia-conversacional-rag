import os
import json
import re
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup
import tiktoken

CHECKPOINT_FILE = Path(__file__).parent / ".ingest_checkpoint"

# Inicializa tokenizer para contagem precisa de tokens (modelo cl100k_base usado pelo gpt-4o/text-embedding-3)
tokenizer = tiktoken.get_encoding("cl100k_base")

# Configuração de Logging Profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ingestion_graph.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configurações via Variáveis de Ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_corpus_env = os.getenv("CORPUS_DIR")
if _corpus_env:
    CORPUS_DIR = _corpus_env
else:
    # Default: path absoluto relativo ao script
    CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dehon_corpus")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    logger.error("Variáveis de ambiente críticas ausentes!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0, max_retries=2)

WEIGHT_MAP = {
    "ASC": 30, "CON": 20, "DOC": 15, "COR": 10, "ART": 10,
    "1LD": 10, "LC1": 10, "LC2": 10, "LCC": 10, "1LC": 10, "1LC1": 10,
    "NHV": 15, "RSO": 10, "DJU": 10, "EXT": 5, "MIS": 8,
    "NQT": 8, "NTD": 8, "NTO": 8, "ACD": 8, "DIS": 8,
    "REV": 8, "DRD": 8, "ENT": 8, "QSS": 8, "CFL": 8,
    "RET": 8, "APD": 8, "DSS": 8, "EXC": 8, "CHR": 8,
    "PRI": 5, "RMP": 5, "PDR": 5, "SMJ": 5, "MMR": 5,
    "RSC": 5, "PSC": 5, "SVN": 5, "DSP": 5, "ECD": 5,
    "ADP": 5, "ARP": 5, "MSO": 5, "MLA": 5, "NCG": 5,
    "OUTROS": 5
}

LIGATURE_MAP = {
    '\ufb00': 'ff', '\ufb01': 'fi', '\ufb02': 'fl', '\ufb03': 'ffi', '\ufb04': 'ffl',
    '\ufb05': 'ft', '\ufb06': 'st', '\u0132': 'IJ', '\u0133': 'ij',
    '\ufb20': 'ft', '\ufb21': 'st',
}

def normalize_text(text: str) -> str:
    """Normaliza texto removendo artefatos de OCR, ligaduras e excesso de espaços."""
    if not text: return ""
    import unicodedata
    # 1. Expande ligaduras tipográficas de scans antigos
    for lig, replacement in LIGATURE_MAP.items():
        text = text.replace(lig, replacement)
    # 2. Normalização Unicode (NFC) para caracteres compostos
    text = unicodedata.normalize('NFC', text)
    # 3. Remove tags HTML/XML remanescentes
    text = re.sub(r'<[^>]+>', '', text)
    # 4. Remove excesso de espaços e quebras de linha duplicadas
    text = re.sub(r'\s+', ' ', text)
    # 5. Remove caracteres de controle e artefatos comuns de OCR/HTML
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # 6. Remove entidades HTML numéricas remanescentes (&#...;)
    text = re.sub(r'&#?\w{0,10};', '', text)
    # 7. Padroniza aspas e hifens
    text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    return text.strip()

def clean_html_text(html_content: str) -> Dict[int, str]:
    """Extrai parágrafos do HTML e mapeia para seus números (ID pXXX).
    Suporta múltiplos formatos de parágrafo (<p>, <div>, <span>) e identificadores."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts, styles e navegação que não fazem parte do conteúdo
    for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    
    par_map = {}
    
    # Tenta encontrar parágrafos com IDs (p1, p2...)
    for p in soup.find_all(['p', 'div', 'span']):
        # Procura por <a id="p123"> dentro ou antes do parágrafo
        anchor = p.find('a', id=re.compile(r'^p\d+'))
        if anchor:
            try:
                par_num = int(anchor['id'][1:])
                text = p.get_text(separator=' ', strip=True)
                if text:
                    par_map[par_num] = text
            except:
                continue
        else:
            # Fallback: Se não tem ID, mas tem número no span parnum
            span = p.find('span', class_='parnum')
            if span:
                try:
                    par_num = int(span.get_text(strip=True))
                    text = p.get_text(separator=' ', strip=True)
                    if text:
                        par_map[par_num] = text
                except:
                    continue
    
    # Se falhou em mapear IDs, retorna como lista simples indexada
    if not par_map:
        for tag in ['p', 'div']:
            paragraphs = [t.get_text(separator=' ', strip=True) for t in soup.find_all(tag) if t.get_text(separator=' ', strip=True)]
            if paragraphs:
                par_map = {i: text for i, text in enumerate(paragraphs)}
                break
        
    return par_map

def get_entities_for_range(data: Dict, start_par: int, end_par: int) -> Dict[str, List[str]]:
    """Extrai entidades (pessoas, lugares, conceitos) mencionadas em um intervalo de parágrafos."""
    entities = {"people": [], "places": [], "concepts": []}
    
    # Busca maps no root ou no documentRef (Correção de Bug)
    doc_ref = data.get('documentRef', {}) if isinstance(data.get('documentRef'), dict) else {}
    
    maps = {
        "people": data.get('peoplemap') or doc_ref.get('peoplemap') or {},
        "places": data.get('placesmap') or doc_ref.get('placesmap') or {},
        "concepts": data.get('conceptsmap') or doc_ref.get('conceptsmap') or {}
    }
    
    # Se os mapas vierem como string JSON (como vi em alguns arquivos)
    for key, val in maps.items():
        if isinstance(val, str):
            try:
                maps[key] = json.loads(val)
            except:
                maps[key] = {}

    for category, mapping in maps.items():
        if not isinstance(mapping, dict): continue
        for entity_name, mentions in mapping.items():
            if not isinstance(mentions, list): continue
            for mention in mentions:
                par_index = mention.get('par')
                if par_index is not None:
                    try:
                        p_idx = int(par_index)
                        if start_par <= p_idx <= end_par:
                            if entity_name not in entities[category]:
                                entities[category].append(entity_name)
                    except:
                        continue
    
    return entities

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings em lote (2000 dimensões). Trunca por tokens, não caracteres."""
    MAX_TOKENS = 8000
    cleaned_texts = []
    for t in texts:
        tokens = tokenizer.encode(t)
        if len(tokens) > MAX_TOKENS:
            tokens = tokens[:MAX_TOKENS]
            t = tokenizer.decode(tokens)
        cleaned_texts.append(t.replace("\n", " "))
    response = client_openai.embeddings.create(
        input=cleaned_texts, 
        model="text-embedding-3-large",
        dimensions=2000
    )
    return [d.embedding for d in response.data]

def ingest_file(file_path: str):
    logger.info(f"Processando: {os.path.basename(file_path)}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler {file_path}: {e}")
        return

    # Extração de Metadados Base
    ps = data.get('prosearch', {})
    # Algumas vezes prosearch está dentro de documentRef
    if not ps and 'documentRef' in data:
        ps = data['documentRef'].get('prosearch', {})
        
    title = data.get('title') or ps.get('title') or 'Sem Título'
    sigla = data.get('sigla') or (ps.get('dehonquote', '').split()[0] if ps.get('dehonquote') else "OUTROS")
    
    # Conteúdo HTML e Texto
    content_obj = data.get('content', {})
    html_content = content_obj.get('html', '') if isinstance(content_obj, dict) else ''
    
    if not html_content:
        # Fallback para texto puro se não houver HTML
        full_text = content_obj.get('text', '') if isinstance(content_obj, dict) else (content_obj or "")
        par_map = {i: p.strip() for i, p in enumerate(full_text.split('\n')) if p.strip()}
    else:
        par_map = clean_html_text(html_content)

    if not par_map:
        # Fallback: Se não tem HTML estruturado, tenta usar o resumo/conteúdo do prosearch
        summary_text = ps.get('content', '')
        if summary_text:
            logger.info(f"Usando fallback prosearch.content para {os.path.basename(file_path)}")
            par_map = {0: normalize_text(summary_text)}
        else:
            logger.warning(f"Arquivo sem conteúdo detectado: {file_path}")
            return
    else:
        # Normaliza todos os parágrafos coletados
        par_map = {k: normalize_text(v) for k, v in par_map.items()}

    # Chunking Temático baseado em Bookmarks
    bookmarks = data.get('bookmarks') or (data.get('documentRef', {}).get('bookmarks') if isinstance(data.get('documentRef'), dict) else None)
    if isinstance(bookmarks, str):
        try: bookmarks = json.loads(bookmarks)
        except: bookmarks = []
    
    chunks_data = []
    sorted_pars = sorted(par_map.keys())
    
    MAX_CHUNK_TOKENS = 1000
    THEMATIC_OVERLAP_TOKENS = 150

    if bookmarks:
        # Modo Thematic: Usa os limites dos bookmarks, com sub-chunking por token
        for idx, bkm in enumerate(bookmarks):
            start_par = int(bkm.get('par', 0))
            end_par = int(bookmarks[idx+1].get('par')) - 1 if idx + 1 < len(bookmarks) else sorted_pars[-1]

            section_pars = [p for p in sorted_pars if start_par <= p <= end_par]
            if not section_pars:
                continue

            receivers = ps.get('receivers', [])
            destinatario = ps.get('receiver') or ps.get('destinatario')

            # Sub-chunking por token dentro da seção temática
            sub_chunk_pars = []
            sub_token_count = 0
            sub_chunk_idx = 0

            def flush_sub_chunk(s_c_pars, s_c_idx):
                if not s_c_pars:
                    return None
                text = " ".join([par_map[p] for p in s_c_pars])
                if len(text) < 100:
                    return None
                entities = get_entities_for_range(data, s_c_pars[0], s_c_pars[-1])
                return {
                    "content": f"SEÇÃO: {bkm.get('text', 'Geral')}\n\n{text}",
                    "metadata": {
                        "title": title,
                        "section_title": bkm.get('text'),
                        "entities": entities,
                        "receivers": receivers,
                        "destinatario": destinatario,
                        "par_range": [s_c_pars[0], s_c_pars[-1]],
                        "sigla": sigla,
                        "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                        "source_id": os.path.basename(file_path),
                        "chunk_index": idx * 100 + s_c_idx
                    }
                }

            for p_num in section_pars:
                text = par_map[p_num]
                tokens = len(tokenizer.encode(text))

                if tokens > MAX_CHUNK_TOKENS:
                    fragments = split_oversized_paragraph(text, MAX_CHUNK_TOKENS)
                    for frag in fragments:
                        frag_entities = get_entities_for_range(data, p_num, p_num)
                        chunks_data.append({
                            "content": f"SEÇÃO: {bkm.get('text', 'Geral')}\n\n{frag}",
                            "metadata": {
                                "title": title,
                                "section_title": bkm.get('text'),
                                "entities": frag_entities,
                                "receivers": receivers,
                                "destinatario": destinatario,
                                "par_range": [p_num, p_num],
                                "sigla": sigla,
                                "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                                "source_id": os.path.basename(file_path),
                                "chunk_index": idx * 100 + sub_chunk_idx
                            }
                        })
                        sub_chunk_idx += 1
                    continue

                if sub_token_count + tokens > MAX_CHUNK_TOKENS and sub_chunk_pars:
                    chunk = flush_sub_chunk(sub_chunk_pars, sub_chunk_idx)
                    if chunk:
                        chunks_data.append(chunk)
                        sub_chunk_idx += 1

                    overlap_pars = []
                    overlap_tokens = 0
                    for p in reversed(sub_chunk_pars):
                        p_tokens = len(tokenizer.encode(par_map[p]))
                        if overlap_tokens + p_tokens <= THEMATIC_OVERLAP_TOKENS:
                            overlap_pars.insert(0, p)
                            overlap_tokens += p_tokens
                        else:
                            break
                    sub_chunk_pars = overlap_pars
                    sub_token_count = overlap_tokens

                sub_chunk_pars.append(p_num)
                sub_token_count += tokens

            if sub_chunk_pars:
                chunk = flush_sub_chunk(sub_chunk_pars, sub_chunk_idx)
                if chunk:
                    chunks_data.append(chunk)
    else:
        # Modo Sliding Window: Para documentos sem bookmarks (como cartas curtas)
        # Otimizado para densidade de tokens (Token Guard)
        current_chunk_pars = []
        current_token_count = 0
        MAX_TOKENS = MAX_CHUNK_TOKENS
        OVERLAP_TOKENS = THEMATIC_OVERLAP_TOKENS
        
        for p_num in sorted_pars:
            text = par_map[p_num]
            tokens = len(tokenizer.encode(text))
            
            if current_token_count + tokens > MAX_TOKENS and current_chunk_pars:
                # Fecha o chunk atual
                start_par, end_par = current_chunk_pars[0], current_chunk_pars[-1]
                chunk_text = " ".join([par_map[p] for p in current_chunk_pars])
                entities = get_entities_for_range(data, start_par, end_par)
                
                chunks_data.append({
                    "content": chunk_text,
                    "metadata": {
                        "title": title,
                        "entities": entities,
                        "receivers": ps.get('receivers', []),
                        "destinatario": ps.get('receiver') or ps.get('destinatario'),
                        "par_range": [start_par, end_par],
                        "sigla": sigla,
                        "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                        "source_id": os.path.basename(file_path),
                        "chunk_index": len(chunks_data)
                    }
                })
                
                # Reinicia com overlap (mantém parágrafos até atingir o overlap desejado)
                overlap_pars = []
                overlap_tokens = 0
                for p in reversed(current_chunk_pars):
                    p_tokens = len(tokenizer.encode(par_map[p]))
                    if overlap_tokens + p_tokens <= OVERLAP_TOKENS:
                        overlap_pars.insert(0, p)
                        overlap_tokens += p_tokens
                    else:
                        break
                current_chunk_pars = overlap_pars
                current_token_count = overlap_tokens

            current_chunk_pars.append(p_num)
            current_token_count += tokens

        # Adiciona o último fragmento se houver
        if current_chunk_pars:
            start_par, end_par = current_chunk_pars[0], current_chunk_pars[-1]
            chunk_text = " ".join([par_map[p] for p in current_chunk_pars])
            chunks_data.append({
                "content": chunk_text,
                "metadata": {
                    "title": title,
                    "entities": get_entities_for_range(data, start_par, end_par),
                    "receivers": ps.get('receivers', []),
                    "destinatario": ps.get('receiver') or ps.get('destinatario'),
                    "par_range": [start_par, end_par],
                    "sigla": sigla,
                    "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                    "source_id": os.path.basename(file_path),
                    "chunk_index": len(chunks_data)
                }
            })

    # Ingestão no Supabase com Embedding Batching
    batch_size = 50 # Reduzido para evitar timeout com 3072 dimensões
    for i in range(0, len(chunks_data), batch_size):
        batch = chunks_data[i:i + batch_size]
        try:
            embeddings = get_embeddings_batch([c["content"] for c in batch])
            for j, emb in enumerate(embeddings):
                batch[j]["embedding"] = emb
            
            supabase.table("documents").insert(batch).execute()
        except Exception as e:
            logger.error(f"Erro no lote do arquivo {file_path}: {e}")

def split_oversized_paragraph(text: str, max_tokens: int) -> List[str]:
    """Divide um parágrafo grande em fragmentos por sentença, respeitando o limite de tokens."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    fragments = []
    current = []
    current_tokens = 0
    for sent in sentences:
        sent_tokens = len(tokenizer.encode(sent))
        if current_tokens + sent_tokens > max_tokens and current:
            fragments.append(" ".join(current))
            current = []
            current_tokens = 0
        if sent_tokens > max_tokens:
            for i in range(0, len(sent), max_tokens * 3):
                fragments.append(sent[i:i + max_tokens * 3])
            continue
        current.append(sent)
        current_tokens += sent_tokens
    if current:
        fragments.append(" ".join(current))
    return fragments if fragments else [text]

def is_mongodb_id(filename: str) -> bool:
    """True se o nome do arquivo (sem .json) é um ObjectId do MongoDB (24 hex chars)."""
    stem = Path(filename).stem
    return bool(re.fullmatch(r'[0-9a-f]{24}', stem, re.IGNORECASE))

def load_checkpoint() -> Set[str]:
    if CHECKPOINT_FILE.exists():
        done = {line.strip() for line in CHECKPOINT_FILE.read_text().splitlines() if line.strip()}
        logger.info(f"Checkpoint encontrado: {len(done)} arquivos já processados")
        return done
    return set()

def save_checkpoint(filename: str):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(filename + "\n")

def get_ingested_source_ids(supabase: Client) -> Set[str]:
    """Consulta source_ids já presentes no banco."""
    ids: Set[str] = set()
    offset = 0
    limit = 1000
    while True:
        r = supabase.table("documents").select("metadata->>source_id").range(offset, offset + limit - 1).execute()
        if not r.data:
            break
        for row in r.data:
            sid = row.get("source_id")
            if sid:
                ids.add(sid)
        if len(r.data) < limit:
            break
        offset += limit
    logger.info(f"Source_ids já no banco: {len(ids)}")
    return ids

def main():
    parser = argparse.ArgumentParser(description="Ingere corpus Dehon no Supabase")
    parser.add_argument("--resume", "-r", action="store_true", help="Pula arquivos já processados (checkpoint + banco)")
    args = parser.parse_args()

    if not os.path.exists(CORPUS_DIR):
        logger.error(f"Diretório não encontrado: {CORPUS_DIR}")
        return

    checkpoint = load_checkpoint() if args.resume else set()
    ingested_ids = get_ingested_source_ids(supabase) if args.resume else set()

    all_files = sorted(
        f for f in os.listdir(CORPUS_DIR)
        if f.endswith('.json') and not is_mongodb_id(f)
    )
    files_to_process = [os.path.join(CORPUS_DIR, f) for f in all_files]

    already_skipped = checkpoint | ingested_ids
    logger.info(f"Total qualificado: {len(files_to_process)}, já processados: {len(already_skipped)}, pendentes: {len(files_to_process) - len(already_skipped)}")

    for fpath in files_to_process:
        fname = os.path.basename(fpath)
        if args.resume and fname in already_skipped:
            logger.debug(f"Pulando (já processado): {fname}")
            continue
        ingest_file(fpath)
        save_checkpoint(fname)

if __name__ == "__main__":
    main()