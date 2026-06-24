import json
import os
from typing import List, Dict, Any
from src.oracle_db_client import get_oracle_connection
from src.rag.search import get_embedding, extract_person_from_query, concept_processor, get_thematic_boosts

def oracle_search_context(query: str, top_k: int = 5, filter_siglas: List[str] = None,
                   fts_weight: float = None, vec_weight: float = None) -> Dict[str, Any]:
    
    target_people = extract_person_from_query(query)
    expanded_query = concept_processor.expand_query(query)
    
    try:
        embedding = get_embedding(expanded_query)
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return {"context": "", "citations": []}
    
    conn = get_oracle_connection()
    if not conn:
        return {"context": "", "citations": []}
        
    results = []
    try:
        cursor = conn.cursor()
        
        # Oracle 23ai vector syntax
        import array
        vec_array = array.array("f", embedding)
        
        sql = """
            SELECT content, metadata, 1 - VECTOR_DISTANCE(embedding, :emb, COSINE) as similarity
            FROM documents
            ORDER BY VECTOR_DISTANCE(embedding, :emb, COSINE)
            FETCH FIRST :top_k ROWS ONLY
        """
        
        cursor.execute(sql, emb=vec_array, top_k=top_k * 5) # Fetch more for re-ranking
        rows = cursor.fetchall()
        
        for row in rows:
            content_clob, meta_clob, sim = row
            content = content_clob.read() if hasattr(content_clob, "read") else content_clob
            meta_str = meta_clob.read() if hasattr(meta_clob, "read") else meta_clob
            try:
                meta = json.loads(meta_str)
            except:
                meta = {}
                
            if filter_siglas:
                if meta.get("sigla") not in filter_siglas:
                    continue
                    
            results.append({
                "content": content,
                "metadata": meta,
                "similarity": sim
            })
            
    except Exception as e:
        print(f"Erro na busca Oracle: {e}")
    finally:
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
        
        context_parts.append(f"--- FONTE [{ref_num}]: {title} ({sigla}) ---\n{content}")
        
        citations.append({
            "id": ref_num,
            "title": title,
            "sigla": sigla,
            "snippet": content[:200] + "...",
            "score": match.get('similarity', 0),
        })

    return {
        "context": "\n\n".join(context_parts),
        "citations": citations
    }
