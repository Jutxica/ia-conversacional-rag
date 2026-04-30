import os
import json
import re
import time
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup

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
CORPUS_DIR = os.getenv("CORPUS_DIR", "backend/data/dehon_corpus")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    logger.error("Variáveis de ambiente críticas ausentes!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Mapeamento de Pesos de Documentos (Conforme Blueprint)
WEIGHT_MAP = {
    "ASC": 30,  # Obras Ascéticas
    "COR": 10,  # Correspondência
    "CON": 20,  # Conferências
    "DOC": 15,  # Documentos Oficiais
    "ART": 10,  # Artigos / Crônicas
    "OUTROS": 5
}

def clean_html_text(html_content: str) -> Dict[int, str]:
    """Extrai parágrafos do HTML e mapeia para seus números (ID pXXX)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    par_map = {}
    
    # Tenta encontrar parágrafos com IDs (p1, p2...)
    for p in soup.find_all('p'):
        # Procura por <a id="p123"> dentro ou antes do parágrafo
        anchor = p.find('a', id=re.compile(r'^p\d+'))
        if anchor:
            try:
                par_num = int(anchor['id'][1:])
                par_map[par_num] = p.get_text(strip=True)
            except:
                continue
        else:
            # Fallback: Se não tem ID, mas tem número no span parnum
            span = p.find('span', class_='parnum')
            if span:
                try:
                    par_num = int(span.get_text(strip=True))
                    par_map[par_num] = p.get_text(strip=True)
                except:
                    continue
    
    # Se falhou em mapear IDs, retorna como lista simples indexada
    if not par_map:
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        par_map = {i: text for i, text in enumerate(paragraphs)}
        
    return par_map

def get_entities_for_range(data: Dict, start_par: int, end_par: int) -> Dict[str, List[str]]:
    """Extrai entidades (pessoas, lugares, conceitos) mencionadas em um intervalo de parágrafos."""
    entities = {"people": [], "places": [], "concepts": []}
    
    # Mapeamentos no JSON original
    maps = {
        "people": data.get('peoplemap', {}),
        "places": data.get('placesmap', {}),
        "concepts": data.get('conceptsmap', {})
    }
    
    # Se os mapas vierem como string JSON (como vi em alguns arquivos)
    for key, val in maps.items():
        if isinstance(val, str):
            try:
                maps[key] = json.loads(val)
            except:
                maps[key] = {}

    for category, mapping in maps.items():
        for entity_name, mentions in mapping.items():
            for mention in mentions:
                par_index = mention.get('par')
                if par_index is not None and start_par <= int(par_index) <= end_par:
                    if entity_name not in entities[category]:
                        entities[category].append(entity_name)
    
    return entities

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings em lote (3072 dimensões)."""
    cleaned_texts = [t[:8000].replace("\n", " ") for t in texts] # Limite seguro de tokens
    response = client_openai.embeddings.create(
        input=cleaned_texts, 
        model="text-embedding-3-large",
        dimensions=2000 # Limite máximo suportado pelo índice HNSW no pgvector
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
            par_map = {0: summary_text}
        else:
            logger.warning(f"Arquivo sem conteúdo detectado: {file_path}")
            return

    # Chunking Temático baseado em Bookmarks
    bookmarks = data.get('bookmarks') or (data.get('documentRef', {}).get('bookmarks') if isinstance(data.get('documentRef'), dict) else None)
    if isinstance(bookmarks, str):
        try: bookmarks = json.loads(bookmarks)
        except: bookmarks = []
    
    chunks_data = []
    sorted_pars = sorted(par_map.keys())
    
    if bookmarks:
        # Modo Thematic: Usa os limites dos bookmarks
        for idx, bkm in enumerate(bookmarks):
            start_par = int(bkm.get('par', 0))
            # O fim é o início do próximo bookmark ou o último parágrafo
            end_par = int(bookmarks[idx+1].get('par')) - 1 if idx + 1 < len(bookmarks) else sorted_pars[-1]
            
            chunk_text = " ".join([par_map[p] for p in sorted_pars if start_par <= p <= end_par])
            if len(chunk_text) < 100: continue # Ignora fragmentos muito pequenos
            
            entities = get_entities_for_range(data, start_par, end_par)
            
            chunks_data.append({
                "content": f"SEÇÃO: {bkm.get('text', 'Geral')}\n\n{chunk_text}",
                "metadata": {
                    "title": title,
                    "section_title": bkm.get('text'),
                    "entities": entities,
                    "par_range": [start_par, end_par],
                    "sigla": sigla,
                    "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                    "source_id": os.path.basename(file_path),
                    "chunk_index": idx
                }
            })
    else:
        # Modo Sliding Window: Para documentos sem bookmarks (como cartas curtas)
        window_size = 8 # parágrafos
        for i, start_idx in enumerate(range(0, len(sorted_pars), window_size - 2)):
            window_indices = sorted_pars[start_idx:start_idx + window_size]
            start_par, end_par = window_indices[0], window_indices[-1]
            
            chunk_text = " ".join([par_map[p] for p in window_indices])
            entities = get_entities_for_range(data, start_par, end_par)
            
            chunks_data.append({
                "content": chunk_text,
                "metadata": {
                    "title": title,
                    "entities": entities,
                    "par_range": [start_par, end_par],
                    "sigla": sigla,
                    "document_weight": WEIGHT_MAP.get(sigla.split('-')[0], 5),
                    "source_id": os.path.basename(file_path),
                    "chunk_index": i
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

def main():
    if not os.path.exists(CORPUS_DIR):
        logger.error(f"Diretório não encontrado: {CORPUS_DIR}")
        return

    # Filtra por siglas reais para evitar arquivos de metadados hexadecimais
    siglas_validas = ('ASC', 'COR', 'CON', 'ART', 'DOC', 'OSC', 'OSP', 'JRN', 'OEU', 'CSC')
    # Prioriza Obras Sociais e Espirituais no início da carga
    def priority_sort(filename):
        if filename.startswith('OSC-'): return 0
        if filename.startswith('OSP-'): return 1
        if filename.startswith('ASC-'): return 2
        return 3

    all_files = [f for f in os.listdir(CORPUS_DIR) if f.endswith('.json')]
    files_to_process = []
    
    logger.info("Escaneando metadados internos...")
    for fname in all_files:
        fpath = os.path.join(CORPUS_DIR, fname)
        try:
            # Check prefix in filename OR open and check internal name
            if any(s in fname for s in siglas_validas):
                internal_name = fname
            else:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    internal_name = str(data.get("name") or data.get("document") or "")
            
            if any(s in internal_name for s in siglas_validas):
                priority = 3
                files_to_process.append((fpath,))
        except:
            continue

    # Ordenação padrão alfabética (neutra)
    files_to_process.sort(key=lambda x: str(x[0]))
    
    logger.info(f"Total qualificado: {len(files_to_process)}")
    
    for fpath_tuple in files_to_process:
        fpath = fpath_tuple[0]
        ingest_file(fpath)

if __name__ == "__main__":
    main()