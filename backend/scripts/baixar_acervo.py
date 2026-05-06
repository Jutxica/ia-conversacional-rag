import os
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def download_file(doc_id, download_dir):
    url = f"https://www.dehondocsoriginals.org/pdf/{doc_id}.pdf"
    filepath = os.path.join(download_dir, f"{doc_id}.pdf")
    
    if os.path.exists(filepath):
        return f"SKIP: {doc_id}"
    
    try:
        # User-Agent para parecer um navegador
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
            with open(filepath, "wb") as f:
                f.write(response.content)
            # Espera um pouco para não ser bloqueado
            time.sleep(1.5) 
            return f"OK: {doc_id}"
        else:
            return f"ERRO {response.status_code}: {doc_id}"
    except Exception as e:
        return f"FALHA: {doc_id} ({str(e)})"

def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    corpus_dir = os.path.join(base_dir, "backend", "data", "dehon_corpus")
    download_dir = os.path.join(base_dir, "output", "correspondencias_originais_pdf")
    
    os.makedirs(download_dir, exist_ok=True)
    
    print("--- INICIADOR DE DOWNLOAD EM MASSA (Utxica Edition) ---")
    print("Aviso: Este processo é lento para evitar bloqueios no servidor.")
    print(f"Destino: {download_dir}\n")

    arquivos = [f.replace(".json", "") for f in os.listdir(corpus_dir) if f.startswith("COR-") and f.endswith(".json")]
    total = len(arquivos)
    
    print(f"Total de arquivos para baixar: {total}")
    
    # Processar um por um para respeitar o delay e não ser banido
    for i, doc_id in enumerate(arquivos):
        result = download_file(doc_id, download_dir)
        print(f"[{i+1}/{total}] {result}")

if __name__ == "__main__":
    run()
