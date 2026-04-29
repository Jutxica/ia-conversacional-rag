import re
import os
import json
import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Carrega variáveis de ambiente
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, '../../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa Supabase e Modelo
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

print("Modelo OpenAI configurado!")

# Carrega o Siglário e Conceitos (Knowledge Graph Leve)
with open(os.path.join(BASE_DIR, 'siglario.json'), 'r', encoding='utf-8') as f:
    SIGLARIO_DB = json.load(f)['works']

with open(os.path.join(BASE_DIR, 'conceitos.json'), 'r', encoding='utf-8') as f:
    KNOWLEDGE_GRAPH = json.load(f)

# Prefixo de domínio teológico
DOMAIN_PREFIX = KNOWLEDGE_GRAPH.get('_domain_prefix', 'No contexto da teologia dehoniana')

LOGS_PATH = os.path.join(BASE_DIR, 'rag_logs.jsonl')

def detect_intent_and_alpha(query: str):
    query_lower = query.lower()
    documentary_keywords = ["em ", "ano", "data", "carta", "diário", "189", "190", "191"]
    has_sigla = any(sigla.lower() in query_lower for sigla in SIGLARIO_DB.keys())
    return 0.3 if (has_sigla or any(kw in query_lower for kw in documentary_keywords)) else 0.7

def expand_query_with_graph(query: str):
    query_lower = query.lower()
    expansion = ""
    for conceito, relacoes in KNOWLEDGE_GRAPH.items():
        if conceito.startswith('_') or not isinstance(relacoes, dict): continue
        conceito_normalizado = conceito.replace('_', ' ').replace('cao', 'ção')
        if conceito in query_lower or conceito_normalizado in query_lower:
            sinonimos = ", ".join(relacoes.get('sinonimo', []))
            relacionados = ", ".join(relacoes.get('relacionado', []))
            expansion += f" ({sinonimos}. Relacionado: {relacionados})"
    return f"{DOMAIN_PREFIX}: {query}{expansion}"

def log_search_results(query, domain, top_matches, discarded_matches):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": query,
        "domain": domain,
        "selected_chunks": [{"id": m.get('id'), "score": m.get('score'), "sigla": m.get('metadata', {}).get('source_id', '???').split('-')[0]} for m in top_matches]
    }
    with open(LOGS_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

# --- Configurações de Autoridade Temática ---
AUTHORITY_MAP = {}
try:
    with open(os.path.join(os.path.dirname(__file__), 'autoridade_tematica.json'), 'r', encoding='utf-8') as f:
        AUTHORITY_MAP = json.load(f)
except Exception as e:
    print(f"Erro ao carregar mapa de autoridade: {e}")

def get_query_domain(query: str) -> str:
    """Detecta o domínio temático da pergunta para aplicar pesos de autoridade."""
    query = query.lower()
    if any(k in query for k in ['social', 'justiça', 'operário', 'pobre', 'economia', 'capital', 'democracia', 'salário', 'catecismo social']):
        return "justica_social"
    if any(k in query for k in ['reparação', 'oblação', 'coração', 'vítima', 'amor', 'eucaristia', 'sacrifício', 'reparador']):
        return "reparacao_oblacao"
    if any(k in query for k in ['maria', 'nossa senhora', 'virgem', 'mãe', 'rosário', 'mês de maria']):
        return "espiritualidade_mariana"
    if any(k in query for k in ['congregação', 'regra', 'constituição', 'voto', 'scj', 'fundação', 'instituto']):
        return "vida_institucional"
    if any(k in query for k in ['quando', 'quem', 'onde', 'vida', 'nascimento', 'viagem', 'itinerário', 'biografia', 'carta', 'escreveu', 'correspondência']):
        return "historia_biografia"
    return None

def apply_authority_weights(results: list, domain: str, query: str = "") -> list:
    """Aplica pesos de autoridade massivos baseados no domínio temático e citações diretas."""
    query_upper = query.upper()
    
    # 1. Boost por Menção Direta à Obra
    mentioned_sigla = None
    for sigla, info in SIGLARIO_DB.items():
        sig_u = sigla.upper()
        tit_u = info.get('title', '').upper()
        # Simplifica o título para detecção (ex: "VIDA DE AMOR")
        short_title = tit_u.replace('UMA ', '').replace('O ', '').replace('A ', '').replace('AO SAGRADO CORAÇÃO DE JESUS', '').strip()
        
        if sig_u in query_upper or (len(short_title) > 3 and short_title in query_upper):
            mentioned_sigla = sigla
            break

    if not domain and not mentioned_sigla:
        return results
    
    weights = AUTHORITY_MAP.get(domain, {"nucleo": [], "complemento": [], "contexto": []})
    
    for res in results:
        meta = res.get('metadata', {})
        sigla_doc = meta.get('sigla', 'OUTROS')
        
        # Multiplicador Base
        multiplier = 1.0
        
        # A. Boost por Menção Direta (Prioridade Máxima)
        if mentioned_sigla and sigla_doc == mentioned_sigla:
            multiplier *= 100.0  # Boost massivo para a obra mencionada
            
        # B. Boost por Hierarquia Epistemológica (Domínio)
        if domain:
            if sigla_doc in weights.get('nucleo', []):
                multiplier *= 10.0  # Nuclear (Livros Doutrinais)
            elif sigla_doc in weights.get('complemento', []):
                multiplier *= 2.0   # Complemento (Diários/Notas)
            elif sigla_doc in weights.get('contexto', []):
                # Se a pergunta for histórica/biográfica, damos peso forte para as cartas
                if domain == "historia_biografia":
                    multiplier *= 5.0
                else:
                    multiplier *= 1.5   # Peso base maior para cartas não sumirem
        
        # C. Boost por Palavra-Chave (Literal)
        # Se um termo raro (como um nome próprio) aparecer no texto, damos um boost de 1000x
        query_terms = [t.lower() for t in query.split() if len(t) > 3]
        for term in query_terms:
            if term in res['content'].lower():
                multiplier *= 1000.0 # Prioridade absoluta para nomes/termos literais
        
        res['score'] *= multiplier
            
    # Re-ordena por score atualizado
    return sorted(results, key=lambda x: x['score'], reverse=True)

def search_context(query: str, top_k: int = 5):
    """
    Motor de busca híbrido com Roteamento de Autoridade Temática.
    1. Expande a query com o Grafo de Conceitos.
    2. Realiza busca híbrida (vetores + texto) no Supabase.
    3. Aplica Pesos de Autoridade (Núcleo/Complemento/Contexto) baseados no domínio.
    4. Expande o contexto dos top resultados (Janela de Prova).
    """
    expanded_query = expand_query_with_graph(query)
    embedding = get_embedding(expanded_query)
    search_terms = " | ".join([t for t in expanded_query.split() if len(t) > 3])
    
    # 1. Busca Semântica (Vetores)
    vector_results = []
    try:
        rpc_params = {
            'query_embedding': embedding,
            'match_threshold': 0.05,
            'match_count': 20
        }
        res = supabase.rpc("match_documents", rpc_params).execute()
        vector_results = res.data or []
    except Exception as e:
        print(f"Erro na busca vetorial: {e}")

    # 2. Busca Léxica (Texto)
    keyword_results = []
    try:
        res = supabase.table("documents") \
            .select("id, content, metadata") \
            .text_search('content', search_terms) \
            .execute()
        keyword_results = res.data[:20] if res.data else []
    except Exception as e:
        print(f"Erro na busca léxica: {e}")

    # 3. Busca Literal de Emergência (ilike) para nomes próprios
    hard_results = []
    try:
        potential_names = [t for t in query.split() if t[0].isupper() and len(t) > 3]
        for name in potential_names:
            res = supabase.table("documents").select("id, content, metadata").ilike('content', f'%{name}%').limit(50).execute()
            if res.data:
                hard_results.extend(res.data)
    except Exception as e:
        print(f"Erro na busca literal: {e}")

    # 3. Fusão RRF (Reciprocal Rank Fusion)
    k = 60
    combined_scores = {}
    
    # Adiciona resultados vetoriais
    for i, res in enumerate(vector_results):
        rid = res['id']
        score = 1.0 / (k + (i + 1))
        combined_scores[rid] = {"score": score, "data": res}
        
    # Adiciona resultados léxicos (ou soma se já existir)
    for i, res in enumerate(keyword_results):
        rid = res['id']
        score = 1.0 / (k + (i + 1))
        if rid in combined_scores:
            combined_scores[rid]["score"] += score
        else:
            combined_scores[rid] = {"score": score, "data": res}
            
    # Adiciona resultados da Busca Literal (Prioridade Máxima)
    for res in hard_results:
        rid = res['id']
        if rid in combined_scores:
            combined_scores[rid]["score"] += 100.0 # Injeta score massivo
        else:
            combined_scores[rid] = {"score": 100.0, "data": res}
            
    # Converte para lista e ordena
    results = [
        {**item["data"], "score": item["score"]} 
        for item in combined_scores.values()
    ]
    results = sorted(results, key=lambda x: x['score'], reverse=True)

    # 4. APLICAÇÃO DE AUTORIDADE TEMÁTICA (Re-ranking)
    domain = get_query_domain(query)
    if domain or True: # Ativa sempre para checar menções diretas
        results = apply_authority_weights(results, domain, query)
    
    # Seleciona os top_k finais
    results = results[:top_k]

    # Processamento dos resultados e Expansão de Contexto (Janela de Prova)
    context_parts = []
    citations = []
    
    for i, match in enumerate(results):
        meta = match.get('metadata', {})
        source_id = meta.get('source_id')
        chunk_index = meta.get('chunk_index')
        content = match.get('content', '')
        
        full_context_text = content
        
        # Expansão para vizinhos (Look-around)
        if source_id and chunk_index is not None:
            try:
                neighbors = supabase.table("documents") \
                    .select("content, metadata->chunk_index") \
                    .eq("metadata->>source_id", source_id) \
                    .in_("metadata->chunk_index", [chunk_index - 2, chunk_index - 1, chunk_index + 1, chunk_index + 2]) \
                    .execute()
                
                if neighbors.data:
                    # Organiza vizinhos por índice e garante a ordem correta
                    neighbor_map = {int(n['metadata']['chunk_index']): n['content'] for n in neighbors.data}
                    
                    # Reconstrói o bloco de 5 partes (se existirem)
                    full_context_text = ""
                    for idx in range(chunk_index - 2, chunk_index + 3):
                        if idx == chunk_index:
                            full_context_text += f"\n{content}\n"
                        elif idx in neighbor_map:
                            full_context_text += f"\n{neighbor_map[idx]}\n"
            except Exception as e:
                print(f"Erro na expansão de {source_id}: {e}")

        # Formatação de Citação
        ref_num = i + 1
        title = meta.get('title', 'Documento Dehoniano')
        sigla = source_id.split('-')[0] if source_id and '-' in source_id else "OBRA"
        
        context_parts.append(f"--- FONTE [{ref_num}]: {title} ({sigla}) ---\n{full_context_text}")
        
        citations.append({
            "id": str(match.get('id', ref_num)),
            "title": title,
            "sigla": sigla,
            "url": f"https://dehondocs.it/search?id={source_id}" if source_id else "#",
            "snippet": full_context_text
        })

    # Cálculo de Confiança
    avg_score = sum(m.get('score', 0) for m in results) / len(results) if results else 0
    conf_pct = int(min(99, avg_score * 100))
    
    confidence = {
        "level": "Alta" if conf_pct > 80 else "Média" if conf_pct > 50 else "Baixa",
        "percentage": conf_pct,
        "avg_score": round(avg_score, 3)
    }
    
    # Log dos resultados
    log_search_results(query, domain or "Geral", results, [])
    
    return "\n\n".join(context_parts), citations, confidence
