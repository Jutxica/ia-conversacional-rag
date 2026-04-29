import os
import requests
import time
from pathlib import Path

# Configurações
LINKS_FILE = Path(__file__).parent / "links.txt"
DOWNLOAD_DIR = Path(__file__).parent.parent / "docs" / "Dehondocs" / "Downloads_Automativos"

def download_pdfs():
    if not LINKS_FILE.exists():
        print(f"[ERRO] Arquivo {LINKS_FILE} nao encontrado!")
        return

    # Garante que a pasta de destino existe
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with open(LINKS_FILE, "r") as f:
        links = [line.strip() for line in f if line.strip().startswith("http")]

    print(f"--- INICIANDO DOWNLOAD DE {len(links)} ARQUIVOS ---")
    print(f"Destino: {DOWNLOAD_DIR}")
    
    success = 0
    errors = 0

    for i, url in enumerate(links):
        filename = url.split("/")[-1]
        filepath = DOWNLOAD_DIR / filename

        if filepath.exists():
            print(f"[{i+1}/{len(links)}] Ignorando (ja existe): {filename}")
            continue

        try:
            print(f"[{i+1}/{len(links)}] Baixando: {filename}...", end=" ", flush=True)
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print("OK!")
            success += 1
            # Pequena pausa para nao sobrecarregar o servidor
            time.sleep(1)
        except Exception as e:
            print(f"FALHOU! Erro: {e}")
            errors += 1

    print(f"\n--- RELATORIO FINAL ---")
    print(f"Sucesso: {success}")
    print(f"Erros: {errors}")
    print(f"Pasta: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    download_pdfs()
