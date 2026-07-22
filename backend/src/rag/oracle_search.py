import json
import os
from typing import List, Dict, Any
from src.oracle_db_client import get_oracle_connection
from src.rag.search import get_embedding, extract_person_from_query, concept_processor, get_thematic_boosts

def oracle_search_context(query: str, top_k: int = 5, filter_siglas: List[str] = None,
                   fts_weight: float = None, vec_weight: float = None) -> Dict[str, Any]:
    
    target_people = extract_person_from_query(query)
    expanded_query = concept_processor.expand_query(query)
    
    embedding = None
    try:
        embedding = get_embedding(expanded_query)
    except Exception as e:
        print(f"Aviso ao gerar embedding (OpenAI): {e}")
        
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
            sql = """
                SELECT content, metadata, 1 - VECTOR_DISTANCE(embedding, :emb, COSINE) as similarity
                FROM documents
                ORDER BY VECTOR_DISTANCE(embedding, :emb, COSINE)
                FETCH FIRST :top_k ROWS ONLY
            """
            cursor.execute(sql, emb=vec_array, top_k=top_k * 5)
            rows = cursor.fetchall()
            for row in rows:
                content_clob, meta_clob, sim = row
                content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                try:
                    meta = json.loads(meta_str)
                except:
                    meta = {}
                if filter_siglas and meta.get("sigla") not in filter_siglas:
                    continue
                results.append({"content": content, "metadata": meta, "similarity": sim})
        except Exception as e:
            print(f"Aviso na busca por vetor Oracle: {e}")

    # 2. Fallback: Se busca por vetor falhou ou retornou vazia (ex: sem cota OpenAI), executa FTS por palavras-chave
    if not results:
        try:
            print("[ORACLE RAG] Executando fallback por palavras-chave no Oracle DB...")
            stopwords = {'sobre', 'como', 'para', 'onde', 'qual', 'quais', 'quem', 'este', 'esta', 'isto', 'aquilo', 'onde'}
            words = [w for w in query.replace('?', '').replace(',', '').split() if len(w) > 2 and w.lower() not in stopwords]
            if words:
                where_clauses = [f"UPPER(content) LIKE UPPER(:w{i})" for i in range(len(words))]
                sql_fts = f"""
                    SELECT content, metadata, 0.85 as similarity
                    FROM documents
                    WHERE {" AND ".join(where_clauses)}
                    FETCH FIRST :top_k ROWS ONLY
                """
                params = {f"w{i}": f"%{word}%" for i, word in enumerate(words)}
                params["top_k"] = top_k * 3
                cursor.execute(sql_fts, **params)
                rows = cursor.fetchall()
                for row in rows:
                    content_clob, meta_clob, sim = row
                    content = content_clob.read() if hasattr(content_clob, "read") else content_clob
                    meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
                    try:
                        meta = json.loads(meta_str)
                    except:
                        meta = {}
                    if filter_siglas and meta.get("sigla") not in filter_siglas:
                        continue
                    results.append({"content": content, "metadata": meta, "similarity": sim})
        except Exception as fts_err:
            print(f"Erro no fallback FTS Oracle: {fts_err}")

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
            
    # Sort and slice
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k]
    
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
