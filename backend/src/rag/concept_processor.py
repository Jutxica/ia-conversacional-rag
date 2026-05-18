import os
import json
import unicodedata
from typing import List, Dict, Any, Set

def _normalize(text: str) -> str:
    """Remove acentos e converte para minúsculas para comparação case/accent-insensitive."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

class ConceptProcessor:
    def __init__(self):
        self.concepts = {}
        self.load_concepts()

    def load_concepts(self):
        """Carrega o arquivo de conceitos JSON."""
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'conceitos.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.concepts = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar conceitos: {e}")

    def expand_query(self, query: str) -> str:
        """Expande a query original com sinônimos encontrados no mapa de conceitos."""
        query_norm = _normalize(query)
        extra_terms = set()
        
        for key, data in self.concepts.items():
            if key.startswith("_"): continue
            
            all_triggers = [key] + data.get("sinonimo", [])
            if any(_normalize(trigger) in query_norm for trigger in all_triggers):
                extra_terms.update(data.get("sinonimo", []))
                extra_terms.update(data.get("relacionado", [])[:3])
        
        if not extra_terms:
            return query
            
        expansion = " ".join(list(extra_terms))
        return f"{query} {expansion}"

    def get_concept_context(self, query: str) -> str:
        """Gera um pequeno parágrafo de contexto histórico/teológico baseado nos conceitos detectados."""
        query_norm = _normalize(query)
        context_blocks = []
        
        for key, data in self.concepts.items():
            if key.startswith("_"): continue
            
            all_triggers = [key] + data.get("sinonimo", [])
            if any(_normalize(trigger) in query_norm for trigger in all_triggers):
                historico = data.get("historico", [])
                contraste = data.get("contraste", [])
                
                block = f"### Contexto sobre '{key.capitalize()}':\n"
                if historico:
                    block += f"- Evolução: {', '.join(historico[:3])}...\n"
                if contraste:
                    block += f"- Diferenciação: {', '.join(contraste[:2])}\n"
                
                context_blocks.append(block)
        
        return "\n".join(context_blocks)

# Instância global para ser usada pelo backend
processor = ConceptProcessor()
