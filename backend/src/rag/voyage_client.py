import os
import requests
from typing import List

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

def get_voyage_embedding(text: str, model: str = "voyage-3-large") -> List[float]:
    """
    Gera um embedding usando a API oficial da Voyage AI.
    Pode retornar vetores de 1024 dimensões (padrão) para o voyage-3-large.
    """
    if not VOYAGE_API_KEY:
        raise ValueError("VOYAGE_API_KEY não configurada no ambiente.")
    
    text = text.replace("\n", " ")
    
    url = "https://api.voyageai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VOYAGE_API_KEY}"
    }
    
    # Usando o voyage-3-large com 1024 dimensões para máxima precisão multilingue
    payload = {
        "input": [text],
        "model": model,
        "output_dimension": 1024
    }
    
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data["data"][0]["embedding"]
