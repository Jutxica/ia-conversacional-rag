import os
import time
import json
import uuid
import re
from typing import List, Dict
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from docx import Document
from openai import OpenAI

# Carrega variáveis de ambiente
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "dehon-ai-index")
DOCS_DIR = os.path.abspath("backend/docs")
CORPUS_DIR = os.path.abspath("backend/data/dehon_corpus")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa Pinecone e OpenAI
pc = Pinecone(api_key=PINECONE_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

print("Carregando modelo multilingue (paraphrase-multilingual-MiniLM-L12-v2)...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def get_or_create_index():
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Criando novo índice no Pinecone: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)

def clean_page_text(text: str) -> str:
    """Limpeza avançada de OCR e remoção de ruídos."""
    if not text:
        return ""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    return text.strip()

def is_noise_page(text: str) -> bool:
    """Detecta se a página é sumário, índice ou bibliografia."""
    lower_text = text.lower()
    noise_keywords = ["sumário", "índice", "bibliografia", "index", "table des matières", "table of contents"]
    
    words = lower_text.split()
    if len(words) < 20: return True
    
    if any(lower_text.startswith(kw) for kw in noise_keywords):
        return True
        
    return False

def extract_pages_from_file(file_path: str) -> List[Dict]:
    """Extrai texto mantendo o número da página ou dados do JSON."""
    ext = os.path.splitext(file_path)[1].lower()
    pages = []
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                raw_text = page.extract_text()
                if raw_text and not is_noise_page(raw_text):
                    pages.append({"page_num": i + 1, "text": clean_page_text(raw_text)})
        elif ext == '.docx':
            doc = Document(file_path)
            full_text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            pages.append({"page_num": 1, "text": clean_page_text(full_text)})
        elif ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            pages.append({"page_num": 1, "text": clean_page_text(full_text)})
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            raw_text = json_data.get("content", {}).get("text", "")
            if raw_text:
                pages.append({"page_num": 1, "text": clean_page_text(raw_text), "json_data": json_data})
                
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
    
    return pages

def semantic_chunking(pages: List[Dict], ideal_words: int = 500, overlap_words: int = 70) -> List[Dict]:
    """Divide respeitando parágrafos e mantendo a página de origem."""
    chunks = []
    current_chunk_text = []
    current_length = 0
    current_page = 1
    current_json = None
    
    for page_data in pages:
        current_page = page_data["page_num"]
        current_json = page_data.get("json_data")
        paragraphs = page_data["text"].split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            
            words = para.split()
            para_length = len(words)
            
            if current_length + para_length > ideal_words and current_chunk_text:
                chunks.append({
                    "text": " ".join(current_chunk_text),
                    "page": current_page,
                    "json_data": current_json
                })
                
                overlap_length = 0
                overlap_chunk = []
                for p in reversed(current_chunk_text):
                    p_len = len(p.split())
                    if overlap_length + p_len > overlap_words:
                        break
                    overlap_chunk.insert(0, p)
                    overlap_length += p_len
                
                current_chunk_text = overlap_chunk
                current_length = overlap_length
            
            current_chunk_text.append(para)
            current_length += para_length
            
    if current_chunk_text:
        chunks.append({
            "text": " ".join(current_chunk_text),
            "page": current_page,
            "json_data": current_json
        })
        
    return chunks

def extract_native_metadata(json_data: dict, filename: str) -> dict:
    """Extrai metadados estruturados vindos nativamente do JSON do DehonDocs."""
    doc_ref = json_data.get("documentRef", {})
    prosearch = json_data.get("prosearch", {})
    
    author_name = "Desconhecido"
    author_obj = prosearch.get("author")
    if isinstance(author_obj, dict):
        author_name = author_obj.get("name", "Desconhecido")
    elif prosearch.get("authors") and len(prosearch["authors"]) > 0:
        author_name = prosearch["authors"][0]
        
    bible_refs = json_data.get("biblerefs", [])
    bible_refs_str = ", ".join(bible_refs[:5]) if bible_refs else ""
    
    return {
        "title": prosearch.get("title", "Sem Título"),
        "author": author_name,
        "date": prosearch.get("date", ""),
        "dehonquote": prosearch.get("dehonquote", ""),
        "bible_refs": bible_refs_str,
        "document_name": doc_ref.get("name", filename),
        "source_type": "dehondocs_api"
    }

def enrich_metadata(chunk_text: str, filename: str) -> dict:
    """Usa IA para extrair metadados ricos do chunk quando não houver JSON estruturado."""
    prompt = f"""
    Analise este trecho do documento '{filename}' e extraia os seguintes metadados em formato JSON.
    Seja breve e preciso.
    Estrutura esperada:
    {{
      "tema_principal": "...",
      "resumo_chunk": "...",
      "palavras_chave": ["...", "..."],
      "nivel_confianca": "Alto|Medio|Baixo"
    }}
    Trecho:
    {chunk_text[:3000]}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Você é um classificador JSON."},
                      {"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        return json.loads(content)
    except Exception as e:
        print(f"Erro ao enriquecer metadados: {e}")
        return {
            "tema_principal": "Indefinido",
            "resumo_chunk": "Erro na extração",
            "palavras_chave": [],
            "nivel_confianca": "Baixo"
        }

def run_advanced_ingestion():
    index = get_or_create_index()
    
    print(f"Limpando dados antigos do índice {INDEX_NAME}...")
    index.delete(delete_all=True)
    time.sleep(2)
    
    all_files = []
    # Coleta arquivos nativos (PDFs soltos e outros)
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            all_files.append(os.path.join(root, file))
            
    # Coleta a base do Corpus JSON, se existir
    if os.path.exists(CORPUS_DIR):
        for root, dirs, files in os.walk(CORPUS_DIR):
            for file in files:
                if file.endswith('.json'):
                    all_files.append(os.path.join(root, file))
    
    if not all_files:
        print(f"Nenhum arquivo encontrado em {DOCS_DIR} ou {CORPUS_DIR}.")
        return

    total_chunks_processed = 0

    for file_path in all_files:
        file_name = os.path.basename(file_path)
        is_json_corpus = file_path.endswith('.json')
        print(f"\n--- Iniciando Processamento: {file_name} ---")
        
        pages = extract_pages_from_file(file_path)
        if not pages:
            continue
            
        chunks = semantic_chunking(pages)
        print(f"Fragmentação Semântica concluída. Total de chunks gerados: {len(chunks)}")
        
        vectors = []
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data["text"]
            chunk_page = chunk_data["page"]
            json_data = chunk_data.get("json_data")
            
            # Se for JSON, extrai metadados nativamente, senão gasta tokens do ChatGPT
            if json_data:
                metadata_extracted = extract_native_metadata(json_data, file_name)
            else:
                print(f"  > Enriquecendo chunk {i+1}/{len(chunks)} com OpenAI...")
                metadata_extracted = enrich_metadata(chunk_text, file_name)
            
            embedding = model.encode(chunk_text)
            
            metadata = {
                "text": chunk_text,
                "source": file_name,
                "page": chunk_page,
                "url": f"file://{file_name}",
                "ordem_no_documento": i + 1,
                **metadata_extracted
            }
            
            vectors.append({
                "id": f"{file_name}_chunk_{i}",
                "values": embedding.tolist(),
                "metadata": metadata
            })
            total_chunks_processed += 1
            
            if len(vectors) >= 50:
                index.upsert(vectors=vectors)
                vectors = []
                
        if vectors:
            index.upsert(vectors=vectors)
            
        print(f"✓ Documento {file_name} indexado com sucesso.")
            
    print(f"\n=== INGESTÃO AVANÇADA CONCLUÍDA ===")
    print(f"Total de fragmentos (chunks) processados e enriquecidos: {total_chunks_processed}")

if __name__ == "__main__":
    run_advanced_ingestion()
