import os
import requests
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================================
# CONFIGURAÇÕES
# =================================================================
BASE_URL = "https://www.dehondocsoriginals.org"
API_URL = f"{BASE_URL}/api/dehon/fulltext"
OUTPUT_DIR = "data/dehon_corpus_full"
CATEGORY = "cor"
PER_PAGE = 100
MAX_WORKERS = 15  # Aumentado para performance
DELAY_BETWEEN_PAGES = 0.5
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =================================================================
# UTILITÁRIOS
# =================================================================

def parse_date_from_id(doc_id):
    """Tenta extrair a data do ID (ex: COR-1LD-1876-0901-...)"""
    match = re.search(r'-(\d{4})-(\d{2})(\d{2})-', doc_id)
    if match:
        year, month, day = match.groups()
        return f"{day}/{month}/{year}"
    return "N/A"

def clean_content(content):
    """Extrai o texto puro se for um objeto ou string."""
    if isinstance(content, dict):
        return content.get('text', content.get('html', ''))
    return str(content) if content else ""

def is_valid_content(content):
    """Verifica se o conteúdo é útil (não vazio ou erro)."""
    if not content: return False
    text = clean_content(content).strip()
    if not text or len(text) < 100 or "Conteúdo não disponível" in text:
        return False
    return True

# =================================================================
# FUNÇÕES DE API
# =================================================================

def fetch_list_page(page_num):
    payload = {
        "q": "",
        "mode": "words",
        "cats": [CATEGORY],
        "page": page_num,
        "perPage": PER_PAGE
    }
    try:
        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fetch_full_document(doc_id):
    payload = {"q": doc_id, "mode": "exact"}
    try:
        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            data = r.json()
            results = data.get('list', {}).get('results', [])
            return results[0] if results else None
    except:
        pass
    return None

# =================================================================
# PROCESSAMENTO
# =================================================================

def process_item(item_meta):
    doc_id = item_meta.get('name')
    if not doc_id: return

    filepath = os.path.join(OUTPUT_DIR, f"{doc_id}.md")
    
    # Se o arquivo já existe, verifica se ele é válido
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing_content = f.read()
            if is_valid_content(existing_content):
                return # Já temos um arquivo bom

    try:
        full_doc = fetch_full_document(doc_id)
        if not full_doc: return

        # Extração inteligente de metadados
        prosearch = full_doc.get('prosearch', {})
        doc_ref = full_doc.get('documentRef', {})
        
        title = prosearch.get('title') or doc_ref.get('title') or doc_id
        
        # Prioridade de data: metadados da API > Fallback pelo ID
        date = prosearch.get('date') or (doc_ref.get('metadata', {}).get('date') if isinstance(doc_ref, dict) else None)
        if not date or date == 'N/A':
            date = parse_date_from_id(doc_id)

        content_raw = full_doc.get('content')
        if not is_valid_content(content_raw):
            # print(f"  [AVISO] Documento {doc_id} veio sem conteúdo real.")
            return

        content = clean_content(content_raw)
        
        md = f"""# {title}

**ID:** {doc_id}
**Data:** {date}
**URL:** {BASE_URL}/pubblicati/COR/{doc_id}

---

{content}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
            
    except Exception as e:
        print(f"Erro ao processar {doc_id}: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Iniciando download CORRIGIDO de {CATEGORY}...")
    
    first_page = fetch_list_page(1)
    if not first_page:
        print("Erro ao conectar à API.")
        return
        
    list_obj = first_page.get('list', {})
    total_docs = list_obj.get('total', 7036)
    total_pages = list_obj.get('totalPages', 71)
    
    print(f"Total estimado: {total_docs} documentos. Páginas: {total_pages}.")
    
    for p in range(1, total_pages + 1):
        print(f"Página {p}/{total_pages}...", end="\r")
        page_data = fetch_list_page(p)
        if not page_data: continue
        
        items = page_data.get('list', {}).get('results', [])
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process_item, items)
            
    print("\nDownload concluído ou verificado.")

if __name__ == "__main__":
    main()
