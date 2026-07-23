import json
import os
import re
from typing import List, Dict, Any
from src.oracle_db_client import get_oracle_connection
from src.rag.search import get_embedding_with_provider, extract_person_from_query, concept_processor, get_thematic_boosts

def oracle_search_context(query: str, top_k: int = 50, filter_siglas: List[str] = None,
                   fts_weight: float = None, vec_weight: float = None) -> Dict[str, Any]:
    
    target_people = extract_person_from_query(query)
    expanded_query = concept_processor.expand_query(query)
    
    emb_info = get_embedding_with_provider(expanded_query)
    embedding = emb_info.get("embedding")
    provider = emb_info.get("provider")
        
    conn = get_oracle_connection()
    if not conn:
        return {"context": "", "citations": []}
        
    results = []
    cursor = conn.cursor()
    
    # 1. Tentar busca por Vetor (Vector Search)
    if embedding:
        try:
            import array
            vec_array = array.array("f", embedding)
            target_col = "embedding_google" if provider == "google" else "embedding"
            print(f"[ORACLE RAG] Executando Busca Vetorial via Provedor: {provider.upper()} na coluna {target_col}...")
            sql = f"""
                SELECT content, metadata, 1 - VECTOR_DISTANCE({target_col}, :emb, COSINE) as similarity
                FROM documents
                WHERE {target_col} IS NOT NULL
                ORDER BY VECTOR_DISTANCE({target_col}, :emb, COSINE)
                FETCH FIRST :fetch_limit ROWS ONLY
            """
            cursor.execute(sql, emb=vec_array, fetch_limit=max(top_k, 50))
            rows = cursor.fetchall()
            for row in rows:
                content_clob, meta_clob, sim = row
                content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                try:
                    meta = json.loads(meta_str)
                except:
                    meta = {}
                filter_siglas_upper = [s.upper() for s in filter_siglas] if filter_siglas else None
                if filter_siglas_upper and str(meta.get("sigla", "")).upper() not in filter_siglas_upper:
                    continue
                results.append({"content": content, "metadata": meta, "similarity": sim})
        except Exception as e:
            print(f"Aviso na busca por vetor Oracle ({provider}): {e}")

    # 2. Fallback / Complemento FTS: Se busca por vetor retornar poucos resultados ou falhar
    if len(results) < top_k:
        try:
            print(f"[ORACLE RAG] Executando busca FTS expansiva no Oracle DB (encontrados {len(results)} via vetor, buscando até {top_k})...")
            stopwords = {
                'sobre', 'como', 'para', 'onde', 'qual', 'quais', 'quem', 'este', 'esta', 'isto', 'aquilo', 
                'resuma', 'resumo', 'explique', 'explicar', 'explicação', 'fale', 'diga', 'padre', 'dehon', 'joão', 'leão', 
                'quaisquer', 'detalhes', 'relacione', 'conte', 'mostre', 'descreva', 'análise', 'analise', 'uma', 'uns', 'umas'
            }
            raw_words = [w for w in re.sub(r'[^\w\s]', '', query).split() if len(w) > 2 and w.lower() not in stopwords]
            if not raw_words:
                raw_words = [w for w in re.sub(r'[^\w\s]', '', query).split() if len(w) > 3]

            TERM_VARIANTS = {
                'catecismo': ['catecismo', 'catéchisme', 'catechisme'],
                'social': ['social', 'sociale', 'sociaux'],
                'obras': ['obras', 'oeuvres', 'œuvres'],
                'retiro': ['retiro', 'retraite'],
                'diario': ['diario', 'diário', 'journal'],
                'carta': ['carta', 'lettre'],
                'amor': ['amor', 'amour'],
                'reparacao': ['reparacao', 'reparação', 'réparation'],
                'constituido': ['constituido', 'constituído', 'constitué', 'estrutura', 'divisão', 'capítulos'],
            }

            expanded_words = []
            for w in raw_words[:5]:
                w_lower = w.lower()
                expanded_words.append(w)
                if w_lower in TERM_VARIANTS:
                    expanded_words.extend(TERM_VARIANTS[w_lower])

            # Deduplica preservando ordem
            search_terms = []
            for term in expanded_words:
                if term and term not in search_terms:
                    search_terms.append(term)

            if search_terms:
                fts_rows = []
                fetch_per_word = max(15, top_k // max(len(search_terms[:8]), 1))
                for word in search_terms[:8]:
                    sql_word = f"""
                        SELECT content, metadata, 0.85 as similarity
                        FROM documents
                        WHERE UPPER(content) LIKE UPPER(:w) OR UPPER(metadata) LIKE UPPER(:w)
                        FETCH FIRST {fetch_per_word} ROWS ONLY
                    """
                    cursor.execute(sql_word, w=f"%{word}%")
                    fts_rows.extend(cursor.fetchall())

                # Adicionar resultados do FTS evitando duplicatas
                existing_contents = {r["content"][:100] for r in results}
                for row in fts_rows:
                    content_clob, meta_clob, sim = row
                    content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                    if content[:100] in existing_contents:
                        continue
                    existing_contents.add(content[:100])

                    meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                    try:
                        meta = json.loads(meta_str)
                    except:
                        meta = {}
                    filter_siglas_upper = [s.upper() for s in filter_siglas] if filter_siglas else None
                    if filter_siglas_upper and str(meta.get("sigla", "")).upper() not in filter_siglas_upper:
                        continue
                    results.append({"content": content, "metadata": meta, "similarity": sim})
        except Exception as fts_err:
            print(f"Erro na busca FTS expansiva Oracle: {fts_err}")

    conn.close()

    # Re-ranking and boosting logic
    theme_boosts = get_thematic_boosts(query)
    for match in results:
        sigla = match.get('metadata', {}).get('sigla', 'OBRA')
        content = match.get('content', '').lower()
        boost = theme_boosts.get(sigla, 0)
        
        if target_people:
            # simple boost
            for person in target_people:
                if person.lower() in content:
                    boost += 0.40
        
        if boost > 0:
            sim = match['similarity']
            match['similarity'] = sim + ((1.0 - sim) * min(boost, 0.9))
            
    # Re-ranking por pontuação
    sorted_candidates = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)

    # Aplicação de Diversificação por Sigla/Obra (máximo de 20% do top_k por sigla)
    max_per_sigla = max(5, top_k // 5)
    diversified_results = []
    sigla_counts = {}

    for match in sorted_candidates:
        sigla = match.get('metadata', {}).get('sigla', 'OUTROS')
        if sigla_counts.get(sigla, 0) < max_per_sigla:
            diversified_results.append(match)
            sigla_counts[sigla] = sigla_counts.get(sigla, 0) + 1

    # Preenche até o top_k se necessário com os demais candidatos
    if len(diversified_results) < top_k:
        added_ids = {id(m) for m in diversified_results}
        for match in sorted_candidates:
            if id(match) not in added_ids:
                diversified_results.append(match)
                added_ids.add(id(match))
                if len(diversified_results) >= top_k:
                    break

    results = diversified_results[:top_k]
    
    context_parts = []
    citations = []

    for i, match in enumerate(results):
        meta = match.get('metadata', {})
        content = match.get('content', '')
        
        ref_num = i + 1
        title = meta.get('title', 'Documento Dehoniano')
        sigla = meta.get('sigla', 'OBRA')
        
        page_number = meta.get('page') or meta.get('page_number') or meta.get('page_num') or None
        page_url = meta.get('url') or meta.get('source_url') or meta.get('page_url') or None
        destinatario = meta.get('destinatario') or meta.get('recipient') or meta.get('addressee') or meta.get('to') or None

        context_parts.append(f"--- FONTE [{ref_num}]: {title} ({sigla}) ---\n{content}")
        
        citations.append({
            "id": ref_num,
            "title": title,
            "sigla": sigla,
            "destinatario": destinatario,
            "snippet": content[:200] + "...",
            "score": match.get('similarity', 0),
            "page_url": page_url,
            "page_number": page_number
        })

    return {
        "context": "\n\n".join(context_parts),
        "citations": citations
    }
