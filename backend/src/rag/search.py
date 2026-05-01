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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str) -> List[float]:
    """Gera embedding de 2000 dimensões usando o modelo Large (limite do HNSW)."""
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(
        input=[text], 
        model="text-embedding-3-large",
        dimensions=2000
    ).data[0].embedding

def search_context(query: str, top_k: int = 5, filter_siglas: List[str] = None) -> Dict[str, Any]:
    """
    Realiza busca híbrida neutra no Supabase.
    O critério de ordenação é puramente a similaridade semântica e lexical (Teor da Pergunta).
    """
    embedding = get_embedding(query)
    
    # Busca Híbrida via RPC (Vetor + FTS)
    try:
        rpc_params = {
            'query_text': query,
            'query_embedding': embedding,
            'match_count': top_k * 2,
            'full_text_weight': 1.0,
            'vector_weight': 1.0,
        }
        if filter_siglas:
            rpc_params['filter_siglas'] = filter_siglas
            
        res = supabase.rpc('hybrid_search', rpc_params).execute()
        results = res.data or []
        print(f"hybrid_search retornou {len(results)} resultados.")
    except Exception as e:
        print(f"Erro na busca híbrida, tentando fallback vetorial: {e}")
        # Fallback para busca vetorial simples
        try:
            fallback_params = {
                'query_embedding': embedding,
                'match_threshold': 0.1,
                'match_count': top_k * 5 if filter_siglas else top_k,
                'filter': {}
            }
            res = supabase.rpc('match_documents', fallback_params).execute()
            all_results = res.data or []
            
            if filter_siglas:
                results = [r for r in all_results if r.get('metadata', {}).get('sigla') in filter_siglas][:top_k]
            else:
                results = all_results[:top_k]
                
            print(f"Fallback retornou {len(results)} resultados após filtro.")
        except Exception as e2:
            print(f"Fallback também falhou: {e2}")
            results = []

    # Re-ordena e seleciona top_k (Baseado puramente na similaridade retornada pelo banco)
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
