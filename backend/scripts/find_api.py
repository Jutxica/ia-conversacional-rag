import requests
import json
import os

def explore_api():
    url = "https://www.dehondocsoriginals.org/api/dehon/fulltext"
    
    # Payload based on the AngularJS controller's advancedSearch POST request
    payload = {
        "q": "Dehon",
        "mode": "words",
        "cats": [],
        "page": 1,
        "perPage": 10
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        print(f"Buscando dados em: {url}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print("Requisição com sucesso!")
            result = data.get("list", {})
            
            print(f"\nTotal de documentos encontrados: {result.get('total')}")
            print(f"Total de páginas: {result.get('totalPages')}")
            print(f"Página atual: {result.get('currentPage')}")
            
            items = result.get('results', [])
            if items:
                print("\nExemplo do primeiro documento retornado:")
                print(json.dumps(items[0], indent=2, ensure_ascii=False))
            else:
                print("\nNenhum documento retornado na lista.")
                
            # Salvar o resultado completo em um arquivo para análise
            output_file = "api_response_sample.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nResposta completa salva em {output_file} para análise.")
            
        else:
            print("A API retornou um erro:")
            print(data.get("err"))
            
    except Exception as e:
        print(f"Erro ao conectar com a API: {e}")

if __name__ == "__main__":
    explore_api()
