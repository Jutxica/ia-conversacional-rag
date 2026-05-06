import os
import json
from typing import List, Dict, Any, Set

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
        query_lower = query.lower()
        extra_terms = set()
        
        for key, data in self.concepts.items():
            if key.startswith("_"): continue
            
            # Verifica se o nome do conceito ou algum sinônimo está na query
            all_triggers = [key] + data.get("sinonimo", [])
            if any(trigger.lower() in query_lower for trigger in all_triggers):
                # Adiciona sinônimos e termos relacionados para expandir a busca
                extra_terms.update(data.get("sinonimo", []))
                extra_terms.update(data.get("relacionado", [])[:3]) # Pega os 3 primeiros relacionados
        
        if not extra_terms:
            return query
            
        expansion = " ".join(list(extra_terms))
        return f"{query} {expansion}"

    def get_concept_context(self, query: str) -> str:
        """Gera um pequeno parágrafo de contexto histórico/teológico baseado nos conceitos detectados."""
        query_lower = query.lower()
        context_blocks = []
        
        for key, data in self.concepts.items():
            if key.startswith("_"): continue
            
            all_triggers = [key] + data.get("sinonimo", [])
            if any(trigger.lower() in query_lower for trigger in all_triggers):
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
