import requests
import json
import os
import time
import sys
from pathlib import Path

def download_corpus():
    url = "https://www.dehondocsoriginals.org/api/dehon/fulltext"
    
    # Pasta onde os documentos serão salvos (path absoluto)
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "dehon_corpus"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    page = 1
    per_page = 100
    total_pages = 1
    total_docs = 0
    max_retries = 5

    print(f"Iniciando download da base do DehonDocs para: {output_dir}")

    while page <= total_pages:
        payload = {
            "q": "Dehon",
            "mode": "words",
            "cats": [],
            "page": page,
            "perPage": per_page
        }
        
        retries = 0
        while retries <= max_retries:
            try:
                print(f"Buscando página {page} de {total_pages if total_pages > 1 else '?'}")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("success"):
                    print(f"Erro na resposta da API na página {page}: {data.get('err')}")
                    retries += 1
                    time.sleep(5)
                    continue
                
                result = data.get("list", {})
                
                if page == 1:
                    total_pages = result.get("totalPages", 1)
                    print(f"Total de documentos a baixar: {result.get('total')}")
                    print(f"Total de páginas (com {per_page} itens): {total_pages}")
                
                items = result.get("results", [])
                
                if not items:
                    print("Nenhum item retornado nesta página. Encerrando.")
                    total_pages = page  # Sai do loop
                    break
                    
                for item in items:
                    doc_ref = item.get("documentRef", {})
                    filename = doc_ref.get("name", item.get("_id", f"doc_pag{page}_{total_docs}"))
                    
                    safe_filename = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in filename]) + ".json"
                    filepath = output_dir / safe_filename
                    
                    if not filepath.exists():
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(item, f, indent=2, ensure_ascii=False)
                    
                    total_docs += 1
                
                print(f"Página {page} concluída. Documentos salvos até agora: {total_docs}")
                page += 1
                time.sleep(1)
                break  # Sai do loop de retry
                
            except Exception as e:
                retries += 1
                print(f"Erro na página {page} (tentativa {retries}/{max_retries}): {e}")
                if retries > max_retries:
                    print(f"Falha após {max_retries} tentativas na página {page}. Pulando...")
                    page += 1
                    break
                time.sleep(5)
            
    print(f"\nDownload finalizado! Total de {total_docs} documentos processados e salvos em {output_dir}")

if __name__ == "__main__":
    download_corpus()
