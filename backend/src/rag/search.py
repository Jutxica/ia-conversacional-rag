import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validação e Inicialização de Clientes
supabase: Client = None
client_openai: OpenAI = None

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("AVISO: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY ausentes!")
    else:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Cliente Supabase inicializado com sucesso.")
except Exception as e:
    print(f"ERRO ao inicializar Supabase: {e}")

try:
    if not OPENAI_API_KEY:
        print("AVISO: OPENAI_API_KEY ausente em search.py!")
    else:
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
        print("Cliente OpenAI inicializado com sucesso em search.py.")
except Exception as e:
    print(f"ERRO ao inicializar OpenAI em search.py: {e}")

def get_embedding(text: str) -> List[float]:
    """Gera embedding de 2000 dimensões usando o modelo Large (limite do HNSW)."""
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(
        input=[text], 
        model="text-embedding-3-large",
        dimensions=2000
    ).data[0].embedding

def get_thematic_boosts(query: str) -> Dict[str, float]:
    """Analisa a query e retorna um mapa de sigla -> boost baseado na autoridade tematica."""
    boosts = {}
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'autoridade_tematica.json')
        if not os.path.exists(json_path):
            return {}
            
        with open(json_path, 'r', encoding='utf-8') as f:
            authority_map = json.load(f)
            
        query_lower = query.lower()
        for theme, data in authority_map.items():
            # Verifica se algum gatilho (trigger) está na query
            if any(trigger in query_lower for trigger in data.get('triggers', [])):
                print(f"  [ALGO] Tema detectado: {theme}. Aplicando pesos de autoridade.")
                weights = data.get('weights', {})
                for level, config in weights.items():
                    boost_val = config.get('boost', 0)
                    for sigla in config.get('siglas', []):
                        # Mantém o maior boost se a sigla aparecer em múltiplos temas
                        boosts[sigla] = max(boosts.get(sigla, 0), boost_val)
    except Exception as e:
        print(f"Erro ao processar autoridade tematica: {e}")
    return boosts

def search_context(query: str, top_k: int = 5, filter_siglas: List[str] = None) -> Dict[str, Any]:
    """
    Realiza busca híbrida e aplica boosting por autoridade temática.
    """
    if not supabase or not client_openai:
        print("Erro: Clientes de busca não inicializados corretamente.")
        return {"context": "", "citations": []}

    try:
        embedding = get_embedding(query)
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return {"context": "", "citations": []}
    
    # Busca Híbrida via RPC (Vetor + FTS)
    try:
        rpc_params = {
            'query_text': query,
            'query_embedding': embedding,
            'match_count': top_k * 5, # Pega mais para permitir o re-rank pelo boost
            'full_text_weight': 1.0,
            'vector_weight': 1.0,
        }
        if filter_siglas:
            rpc_params['filter_siglas'] = filter_siglas
            
        res = supabase.rpc('hybrid_search', rpc_params).execute()
        results = res.data or []
    except Exception as e:
        print(f"Erro na busca híbrida, tentando fallback: {e}")
        results = []

    # --- NOVO: Lógica de Autoridade Temática (Boosting) ---
    theme_boosts = get_thematic_boosts(query)
    
    for match in results:
        sigla = match.get('metadata', {}).get('sigla', 'OBRA')
        boost = theme_boosts.get(sigla, 0)
        if boost > 0:
            original_score = match.get('similarity', 0)
            match['similarity'] = original_score + boost
            # print(f"    Boost em {sigla}: {original_score:.3f} -> {match['similarity']:.3f}")

    # Re-ordena após o boost e seleciona top_k
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k]

    context_parts = []
    citations = []
    
    for i, match in enumerate(results):
        meta = match.get('metadata', {})
        source_id = meta.get('source_id')
        chunk_index = meta.get('chunk_index')
        content = match.get('content', '')
        
        full_context_text = content
        
        # Expansão de contexto para vizinhos (Look-around)
        if source_id and chunk_index is not None:
            try:
                # Busca o parágrafo anterior e posterior para dar mais fluidez à resposta
                neighbors = supabase.table("documents") \
                    .select("content, metadata->chunk_index") \
                    .eq("metadata->>source_id", source_id) \
                    .in_("metadata->chunk_index", [chunk_index - 1, chunk_index + 1]) \
                    .execute()
                
                if neighbors.data:
                    neighbor_map = {int(n['metadata']['chunk_index']): n['content'] for n in neighbors.data}
                    parts = []
                    if chunk_index - 1 in neighbor_map: parts.append(neighbor_map[chunk_index - 1])
                    parts.append(content)
                    if chunk_index + 1 in neighbor_map: parts.append(neighbor_map[chunk_index + 1])
                    full_context_text = "\n[...]\n".join(parts)
            except:
                pass

        ref_num = i + 1
        title = meta.get('title', 'Documento Dehoniano')
        sigla = meta.get('sigla', 'OBRA')
        destinatario = meta.get('destinatario') or meta.get('recipient') or meta.get('addressee') or meta.get('to') or None
        data_doc = meta.get('date') or meta.get('data') or meta.get('year') or None
        page_url = meta.get('url') or meta.get('source_url') or meta.get('page_url') or None
        page_number = meta.get('page') or meta.get('page_number') or meta.get('page_num') or None
        
        context_parts.append(f"--- FONTE [{ref_num}]: {title} ({sigla}) ---\n{full_context_text}")
        
        citations.append({
            "id": ref_num,
            "title": title,
            "sigla": sigla,
            "destinatario": destinatario,
            "data": data_doc,
            "snippet": content,
            "score": match.get('similarity', 0),
            "page_url": page_url,
            "page_number": page_number
        })


    return {
        "context": "\n\n".join(context_parts),
        "citations": citations
    }
