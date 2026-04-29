import requests
import json
import os
import time

def download_corpus():
    url = "https://www.dehondocsoriginals.org/api/dehon/fulltext"
    
    # Pasta onde os documentos serão salvos
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dehon_corpus")
    os.makedirs(output_dir, exist_ok=True)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    page = 1
    per_page = 100  # Vamos tentar puxar 100 por vez para acelerar
    total_pages = 1
    total_docs = 0

    print(f"Iniciando download da base do DehonDocs para: {output_dir}")

    while page <= total_pages:
        payload = {
            "q": "Dehon",
            "mode": "words",
            "cats": [],
            "page": page,
            "perPage": per_page
        }
        
        try:
            print(f"Buscando página {page} de {total_pages if total_pages > 1 else '?'}")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                result = data.get("list", {})
                
                # Atualizar o total de páginas na primeira requisição
                if page == 1:
                    total_pages = result.get("totalPages", 1)
                    print(f"Total de documentos a baixar: {result.get('total')}")
                    print(f"Total de páginas (com {per_page} itens): {total_pages}")
                
                items = result.get("results", [])
                
                if not items:
                    print("Nenhum item retornado nesta página. Encerrando.")
                    break
                    
                for item in items:
                    # Tentar usar o nome do documento como nome de arquivo, ou o ID como fallback
                    doc_ref = item.get("documentRef", {})
                    filename = doc_ref.get("name", item.get("_id", f"doc_pag{page}_{total_docs}"))
                    
                    # Garantir que o nome do arquivo seja seguro
                    safe_filename = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in filename]) + ".json"
                    filepath = os.path.join(output_dir, safe_filename)
                    
                    # Salvar apenas se ainda não existir (permite resumir o script)
                    if not os.path.exists(filepath):
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(item, f, indent=2, ensure_ascii=False)
                    
                    total_docs += 1
                
                print(f"Página {page} concluída. Documentos salvos até agora: {total_docs}")
                page += 1
                
                # Pequeno delay para não sobrecarregar o servidor deles
                time.sleep(1)
                
            else:
                print(f"Erro na resposta da API na página {page}: {data.get('err')}")
                # Pode tentar continuar se for um erro específico
                break
                
        except Exception as e:
            print(f"Erro na conexão na página {page}: {e}")
            print("Aguardando 5 segundos antes de tentar novamente...")
            time.sleep(5)
            # Tentar novamente a mesma página
            
    print(f"\nDownload finalizado! Total de {total_docs} documentos processados e salvos em {output_dir}")

if __name__ == "__main__":
    download_corpus()
