import json
import os
import re
from typing import List, Dict, Any
from src.oracle_db_client import get_oracle_connection
from src.rag.search import get_embedding_with_provider, extract_person_from_query, concept_processor, get_thematic_boosts

def get_source_type(metadata: dict) -> str:
    sigla = str(metadata.get("sigla", "")).upper().strip()
    title = str(metadata.get("title", "")).upper().strip()
    doc_name = str(metadata.get("document_name", "")).upper().strip()
    source_id = str(metadata.get("source_id", "")).upper().strip()
    
    # Identify secondary sources (Studia Dehoniana, biography, essays)
    secondary_indicators = ["STD", "STUDIA", "HOMEM DE IGREJA", "COMENTADOR", "1_FR.PDF", "2_FR.PDF", "3_FR.PDF"]
    for indicator in secondary_indicators:
        if (indicator in sigla) or (indicator in title) or (indicator in doc_name) or (indicator in source_id):
            return "secondary"
            
    if sigla.endswith(".PDF") or len(sigla) > 10:
        return "secondary"
        
    return "primary"

def oracle_search_context(query: str, top_k: int = 50, filter_siglas: List[str] = None,
                   fts_weight: float = None, vec_weight: float = None, intent: str = None) -> Dict[str, Any]:
    
    target_people = extract_person_from_query(query)
    expanded_query = concept_processor.expand_query(query)
    
    emb_info = get_embedding_with_provider(expanded_query)
    embedding = emb_info.get("embedding")
    provider = emb_info.get("provider")
        
    conn = get_oracle_connection()
    if not conn:
        return {"context": "", "citations": []}
        
    cursor = conn.cursor()
    
    # 1. Determine target limits for primary and secondary sources based on intent
    if intent == "citação literal":
        secondary_limit = 0
        primary_limit = top_k
    elif intent == "biografia/factual":
        secondary_limit = int(top_k * 0.20)
        primary_limit = top_k - secondary_limit
    elif intent == "interpretação/análise":
        secondary_limit = int(top_k * 0.40)
        primary_limit = top_k - secondary_limit
    else:  # geral
        secondary_limit = int(top_k * 0.30)
        primary_limit = top_k - secondary_limit

    # We fetch more to allow for Python-side filtering/diversification/leakage handling
    fetch_primary = max(primary_limit * 3, 100)
    fetch_secondary = max(secondary_limit * 3, 100) if secondary_limit > 0 else 0

    primary_results = []
    secondary_results = []
    
    # Vector Search
    if embedding:
        try:
            import array
            vec_array = array.array("f", embedding)
            
            # Fetch Primary candidates (where sigla != 'OBRA' and title/document name doesn't contain STD/STUDIA)
            sql_primary = """
                SELECT content, metadata, 1 - VECTOR_DISTANCE(embedding, :emb, COSINE) as similarity
                FROM documents
                WHERE embedding IS NOT NULL
                  AND (JSON_VALUE(metadata, '$.sigla') IS NULL OR JSON_VALUE(metadata, '$.sigla') != 'OBRA')
                  AND (JSON_VALUE(metadata, '$.document_name') IS NULL OR (UPPER(JSON_VALUE(metadata, '$.document_name')) NOT LIKE '%STD%' AND UPPER(JSON_VALUE(metadata, '$.document_name')) NOT LIKE '%STUDIA%'))
                ORDER BY VECTOR_DISTANCE(embedding, :emb, COSINE)
                FETCH FIRST :fetch_limit ROWS ONLY
            """
            cursor.execute(sql_primary, emb=vec_array, fetch_limit=fetch_primary)
            for row in cursor.fetchall():
                content_clob, meta_clob, sim = row
                content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                try:
                    meta = json.loads(meta_str)
                except:
                    meta = {}
                source_type = get_source_type(meta)
                meta["source_type"] = source_type
                
                # Double-check classification via Python
                if source_type == "primary":
                    primary_results.append({"content": content, "metadata": meta, "similarity": sim})
                else:
                    if secondary_limit > 0:
                        secondary_results.append({"content": content, "metadata": meta, "similarity": sim})
                
            # Fetch Secondary candidates
            if fetch_secondary > 0:
                sql_secondary = """
                    SELECT content, metadata, 1 - VECTOR_DISTANCE(embedding, :emb, COSINE) as similarity
                    FROM documents
                    WHERE embedding IS NOT NULL
                      AND (JSON_VALUE(metadata, '$.sigla') = 'OBRA'
                           OR UPPER(JSON_VALUE(metadata, '$.document_name')) LIKE '%STD%'
                           OR UPPER(JSON_VALUE(metadata, '$.document_name')) LIKE '%STUDIA%')
                    ORDER BY VECTOR_DISTANCE(embedding, :emb, COSINE)
                    FETCH FIRST :fetch_limit ROWS ONLY
                """
                cursor.execute(sql_secondary, emb=vec_array, fetch_limit=fetch_secondary)
                for row in cursor.fetchall():
                    content_clob, meta_clob, sim = row
                    content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                    meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                    try:
                        meta = json.loads(meta_str)
                    except:
                        meta = {}
                    source_type = get_source_type(meta)
                    meta["source_type"] = source_type
                    
                    if source_type == "secondary":
                        secondary_results.append({"content": content, "metadata": meta, "similarity": sim})
                    else:
                        primary_results.append({"content": content, "metadata": meta, "similarity": sim})
                    
        except Exception as e:
            print(f"Erro na busca por vetor Oracle: {e}")

    # Fallback/Complement FTS: if either cota is not filled
    if len(primary_results) < primary_limit or (secondary_limit > 0 and len(secondary_results) < secondary_limit):
        try:
            print(f"[ORACLE RAG] Executando busca FTS expansiva no Oracle DB para completar cotas...")
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

            search_terms = []
            for term in expanded_words:
                if term and term not in search_terms:
                    search_terms.append(term)

            if search_terms:
                existing_primary = {r["content"][:100] for r in primary_results}
                existing_secondary = {r["content"][:100] for r in secondary_results}
                
                # Fetch FTS results and classify
                for word in search_terms[:5]:
                    sql_fts = """
                        SELECT content, metadata, 0.85 as similarity
                        FROM documents
                        WHERE UPPER(DBMS_LOB.SUBSTR(content, 4000, 1)) LIKE UPPER(:w) 
                           OR UPPER(DBMS_LOB.SUBSTR(metadata, 4000, 1)) LIKE UPPER(:w)
                        FETCH FIRST 50 ROWS ONLY
                    """
                    cursor.execute(sql_fts, w=f"%{word}%")
                    for row in cursor.fetchall():
                        content_clob, meta_clob, sim = row
                        content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                        
                        meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                        try:
                            meta = json.loads(meta_str)
                        except:
                            meta = {}
                        
                        source_type = get_source_type(meta)
                        meta["source_type"] = source_type
                        
                        if source_type == "primary":
                            if content[:100] not in existing_primary:
                                primary_results.append({"content": content, "metadata": meta, "similarity": sim})
                                existing_primary.add(content[:100])
                        else:
                            if secondary_limit > 0 and content[:100] not in existing_secondary:
                                secondary_results.append({"content": content, "metadata": meta, "similarity": sim})
                                existing_secondary.add(content[:100])
                                
        except Exception as fts_err:
            print(f"Erro na busca FTS: {fts_err}")

    conn.close()

    # Re-ranking and boosting logic (separate for primary and secondary lists)
    theme_boosts = get_thematic_boosts(query)
    
    def apply_boosting(candidates_list):
        for match in candidates_list:
            sigla = match.get('metadata', {}).get('sigla', 'OBRA')
            content = match.get('content', '').lower()
            boost = theme_boosts.get(sigla, 0)
            
            source_type = match.get('metadata', {}).get('source_type', 'primary')
            if source_type == 'primary':
                boost += 0.15
                
            if target_people:
                for person in target_people:
                    if person.lower() in content:
                        boost += 0.40
            
            if boost > 0:
                sim = match['similarity']
                match['similarity'] = sim + ((1.0 - sim) * min(boost, 0.9))

    apply_boosting(primary_results)
    apply_boosting(secondary_results)

    # Apply filter_siglas in Python
    if filter_siglas:
        filter_siglas_upper = [s.upper() for s in filter_siglas]
        def filter_by_siglas(lst):
            filtered = []
            for match in lst:
                meta = match.get('metadata', {})
                meta_sigla = str(meta.get("sigla", "")).upper()
                meta_code = str(meta.get("url_code", "")).upper()
                meta_cat = str(meta.get("category", "")).upper()
                allowed = any(s in meta_sigla or meta_sigla in s or s in meta_code or s in meta_cat for s in filter_siglas_upper)
                if allowed:
                    filtered.append(match)
            return filtered
            
        primary_results = filter_by_siglas(primary_results)
        secondary_results = filter_by_siglas(secondary_results)

    # Sort each list by similarity
    sorted_primary = sorted(primary_results, key=lambda x: x.get('similarity', 0), reverse=True)
    sorted_secondary = sorted(secondary_results, key=lambda x: x.get('similarity', 0), reverse=True)

    # Select and diversify candidates
    max_per_sigla = max(5, top_k // 5)
    
    def select_with_diversification(candidates, limit):
        selected = []
        sigla_counts = {}
        # First pass: diversified
        for match in candidates:
            sigla = match.get('metadata', {}).get('sigla', 'OUTROS')
            if sigla_counts.get(sigla, 0) < max_per_sigla:
                selected.append(match)
                sigla_counts[sigla] = sigla_counts.get(sigla, 0) + 1
                if len(selected) >= limit:
                    break
        # Second pass: fill up remaining
        if len(selected) < limit:
            added_ids = {id(m) for m in selected}
            for match in candidates:
                if id(match) not in added_ids:
                    selected.append(match)
                    added_ids.add(id(match))
                    if len(selected) >= limit:
                        break
        return selected

    final_primary = select_with_diversification(sorted_primary, primary_limit)
    final_secondary = select_with_diversification(sorted_secondary, secondary_limit) if secondary_limit > 0 else []

    # Merge and sort final results
    results = final_primary + final_secondary
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
    
    context_parts = []
    citations = []

    for i, match in enumerate(results):
        meta = match.get('metadata', {})
        content = match.get('content', '')
        
        ref_num = i + 1
        title = meta.get('title', 'Documento Dehoniano')
        sigla = meta.get('sigla', 'OBRA')
        source_type = meta.get('source_type', 'primary')
        source_type_label = "PRIMÁRIA" if source_type == "primary" else "SECUNDÁRIA"
        
        page_number = meta.get('page') or meta.get('page_number') or meta.get('page_num') or None
        page_url = meta.get('url') or meta.get('source_url') or meta.get('page_url') or None
        destinatario = meta.get('destinatario') or meta.get('recipient') or meta.get('addressee') or meta.get('to') or None

        context_parts.append(f"--- FONTE [{ref_num}] ({source_type_label}): {title} ({sigla}) ---\n{content}")
        
        citations.append({
            "id": ref_num,
            "title": title,
            "sigla": sigla,
            "destinatario": destinatario,
            "snippet": content[:200] + "...",
            "content": content,
            "score": match.get('similarity', 0),
            "page_url": page_url,
            "page_number": page_number,
            "source_type": source_type
        })

    return {
        "context": "\n\n".join(context_parts),
        "citations": citations
    }
