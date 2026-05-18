import os
import time
from typing import List, Dict, Any

class DehonReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_attempts = 0
        self._max_load_attempts = 3
        
    def _load_model(self):
        if self.model is not None:
            return
        enable_reranker = os.getenv("ENABLE_RERANKER", "true").lower() == "true"
        if not enable_reranker:
            print("  [RERANK] Re-ranker desativado via configuração (Economia de Memória).")
            self.model = "DISABLED"
            return

        while self._load_attempts < self._max_load_attempts:
            self._load_attempts += 1
            print(f"  [RERANK] Carregando modelo Cross-Encoder ({self._load_attempts}/{self._max_load_attempts}): {self.model_name}...")
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(self.model_name)
                print("  [RERANK] Modelo carregado com sucesso.")
                return
            except Exception as e:
                print(f"  [ERRO RERANK] Tentativa {self._load_attempts} falhou: {e}")
                if self._load_attempts < self._max_load_attempts:
                    wait = 2 ** self._load_attempts
                    print(f"  [RERANK] Aguardando {wait}s para nova tentativa...")
                    time.sleep(wait)
        print(f"  [RERANK] Falha após {self._max_load_attempts} tentativas. Re-ranker desativado.")
        self.model = "FAILED"

    def rerank(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Re-ranqueia os resultados usando um Cross-Encoder para maior precisão semântica.
        """
        if not results:
            return []

        self._load_model()
        
        if self.model is None or self.model in ("FAILED", "DISABLED"):
            return results[:top_k]
        
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
