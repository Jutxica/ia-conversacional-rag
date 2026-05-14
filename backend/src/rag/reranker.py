import os
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class DehonReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        # O modelo será carregado sob demanda para evitar overhead se não for usado
        
    def _load_model(self):
        if self.model is None:
            print(f"  [RERANK] Carregando modelo Cross-Encoder: {self.model_name}...")
            self.model = CrossEncoder(self.model_name)
            print("  [RERANK] Modelo carregado com sucesso.")

    def rerank(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Re-ranqueia os resultados usando um Cross-Encoder para maior precisão semântica.
        """
        if not results:
            return []

        self._load_model()
        
        # Prepara os pares (query, documento) para o Cross-Encoder
        # Usamos o conteúdo do documento para o scoring
        pairs = [[query, r.get('content', '')] for r in results]
        
        # Gera os scores (quanto maior, mais relevante)
        scores = self.model.predict(pairs)
        
        # Atualiza os scores nos resultados
        for i, score in enumerate(scores):
            # Normalização simples do score do Cross-Encoder (sigmoide para 0-1)
            # O MiniLM-L-6-v2 gera scores que podem ser negativos ou positivos altos
            import numpy as np
            norm_score = 1 / (1 + np.exp(-score))
            
            # Combinamos o score original (híbrido) com o do Cross-Encoder
            # Peso maior para o Cross-Encoder pois ele é "mais inteligente"
            original_score = results[i].get('similarity', 0)
            results[i]['similarity'] = (original_score * 0.3) + (norm_score * 0.7)
            results[i]['rerank_score'] = float(norm_score)
            results[i]['cross_encoder_raw'] = float(score)

        # Ordena novamente pelos novos scores
        reranked_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
        
        return reranked_results[:top_k]

reranker = DehonReranker()
