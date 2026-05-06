import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
from src.rag.concept_processor import processor as concept_processor

# Carrega configurações
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
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

def extract_person_from_query(query: str) -> List[str]:
    """Tenta identificar se a query menciona uma pessoa do nosso dicionário de conceitos."""
    people_detected = []
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'conceitos.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
            
            query_lower = query.lower()
            for key, data in concepts.items():
                if key.startswith("_"): continue
                
                # Sinônimos e variações
                synonyms = data.get("sinonimo", [])
                all_names = [key] + synonyms
                
                # Se for um conceito de pessoa (identificado por ter nomes próprios ou na categoria certa)
                # No conceitos.json, pessoas como andre_prevot, ressel, dupanloup etc.
                is_person = any(c.isupper() for c in key if c.isalpha()) or key in ["ressel", "prevot", "andre_prevot"]
                
                if is_person:
                    for name in all_names:
                        # Busca exata ou com "Pe." / "Padre"
                        if name.lower() in query_lower:
                            people_detected.append(name)
                            break
    except Exception as e:
        print(f"Erro na extração de pessoas: {e}")
    return list(set(people_detected))

def search_context(query: str, top_k: int = 5, filter_siglas: List[str] = None) -> Dict[str, Any]:
    """
    Realiza busca híbrida e aplica boosting por autoridade temática e destinatários.
    """
    if not supabase or not client_openai:
        print("Erro: Clientes de busca não inicializados corretamente.")
        return {"context": "", "citations": []}

    # --- NOVO: Detecção de Destinatários/Pessoas ---
    target_people = extract_person_from_query(query)
    if target_people:
        print(f"  [ALGO] Destinatários detectados: {target_people}")

    # --- NOVO: Expansão de Query (Sinônimos Dehonianos) ---
    expanded_query = concept_processor.expand_query(query)
    if expanded_query != query:
        print(f"  [ALGO] Query expandida: {expanded_query}")

    try:
        embedding = get_embedding(expanded_query)
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return {"context": "", "citations": []}
    
    # Busca Híbrida via RPC (Vetor + FTS)
    try:
        rpc_params = {
            'query_text': expanded_query,
            'query_embedding': embedding,
            'match_count': top_k * 5,
            'full_text_weight': 1.0,
            'vector_weight': 1.0,
        }
        if filter_siglas:
            rpc_params['filter_siglas'] = filter_siglas
        
        if target_people:
            rpc_params['target_entities'] = target_people
            
        try:
            res = supabase.rpc('hybrid_search', rpc_params).execute()
        except Exception as e:
            if "target_entities" in str(e):
                # Fallback se a função no DB ainda não foi atualizada
                print("  [AVISO] RPC 'hybrid_search' antigo detectado. Usando fallback sem target_entities.")
                rpc_params.pop('target_entities')
                res = supabase.rpc('hybrid_search', rpc_params).execute()
            else:
                raise e
                
        results = res.data or []
    except Exception as e:
        print(f"Erro na busca híbrida: {e}")
        results = []

    # --- NOVO: Lógica de Autoridade Temática e Destinatários (Boosting) ---
    theme_boosts = get_thematic_boosts(query)
    
    for match in results:
        sigla = match.get('metadata', {}).get('sigla', 'OBRA')
        content = match.get('content', '').lower()
        
        # 1. Boost Temático
        boost = theme_boosts.get(sigla, 0)
        
        # 2. Boost de Destinatário/Pessoa (Pesado - Python Side)
        if target_people:
            meta_entities = match.get('metadata', {}).get('entities', {})
            people_in_meta = meta_entities.get('people', [])
            receivers_in_meta = match.get('metadata', {}).get('receivers', [])
            destinatario_str = match.get('metadata', {}).get('destinatario', '') or ''
            
            for person in target_people:
                person_low = person.lower()
                # Verifica no texto, nos metadados de entidades e nos campos de destinatário
                in_content = person_low in content
                in_entities = any(person_low in str(p).lower() for p in people_in_meta)
                in_receivers = any(person_low in str(r).lower() for r in receivers_in_meta)
                is_destinatario = person_low in destinatario_str.lower()
                
                if in_content or in_entities or in_receivers or is_destinatario:
                    boost += 0.80 # Aumenta MUITO a chance de aparecer (mais que o 0.40 anterior)
                    # print(f"    [DEST] Nome {person} encontrado. Boost pesado aplicado.")

        if boost > 0:
            original_score = match.get('similarity', 0)
            match['similarity'] = original_score + boost

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
        
        # Se não tiver link vindo do banco, geramos o link direto para o PDF original
        if not page_url:
            doc_id = meta.get('document') or meta.get('source_id')
            if doc_id:
                # Remove extensão .json se houver
                doc_id_clean = doc_id.replace('.json', '')
                page_url = f"https://www.dehondocsoriginals.org/pdf/{doc_id_clean}.pdf"
        
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
