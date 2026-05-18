import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from src.rag.search import search_context
from src.rag.intent_detector import detector as intent_detector

TEST_QUERIES = [
    "Qual era a visão de Dehon sobre a justiça social e os operários?",
    "Onde e quando nasceu o Padre Leão Dehon?",
    "Explique o conceito de reparação na espiritualidade dehoniana",
    "Qual a relação entre o Sagrado Coração de Jesus e a doutrina social de Dehon?",
    "Quem foi o destinatário da carta 1LD e qual o contexto histórico?",
    "Como Dehon descreve a oblação em seus diários espirituais?",
    "O que é a Congregação dos Sacerdotes do Sagrado Coração de Jesus?",
    "Diferença entre reparação passiva e reparação ativa no pensamento dehoniano",
    "ASC CON COR DOC 1LD siglas significado obras Dehon",
    "Qual a influência da Rerum Novarum no pensamento social de Dehon?",
]

INTENT_CONFIGS = {
    "HISTORICAL": {"fts_weight": 1.5, "vec_weight": 1.0, "top_k": 10},
    "THEOLOGICAL": {"fts_weight": 1.0, "vec_weight": 1.5, "top_k": 8},
    "CITATION": {"fts_weight": 2.0, "vec_weight": 0.5, "top_k": 12},
    "GENERAL": {"fts_weight": 1.0, "vec_weight": 1.0, "top_k": 8},
}

def run_stress_test():
    results = []
    total_start = time.time()

    print(f"{'='*80}")
    print(f"STRESS TEST - BUSCA HÍBRIDA DEHON AI")
    print(f"{'='*80}\n")

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Query: {query[:70]}...")

        intent_result = intent_detector.detect(query)
        intent = intent_result["intent"]
        config = INTENT_CONFIGS.get(intent, INTENT_CONFIGS["GENERAL"])

        q_start = time.time()
        try:
            result = search_context(
                query,
                top_k=config["top_k"],
                fts_weight=config["fts_weight"],
                vec_weight=config["vec_weight"]
            )
            elapsed = time.time() - q_start
            context_len = len(result.get("context", ""))
            num_citations = len(result.get("citations", []))

            print(f"  Intent: {intent} | Tempo: {elapsed:.2f}s | Citações: {num_citations} | Contexto: {context_len} chars")

            if result.get("citations"):
                best = max(result["citations"], key=lambda c: c.get("score", 0))
                print(f"  Melhor score: {best.get('score', 0):.4f} | Fonte: {best.get('title', '?')} ({best.get('sigla', '?')})")

            results.append({
                "query": query,
                "intent": intent,
                "time_seconds": round(elapsed, 3),
                "num_citations": num_citations,
                "context_length": context_len,
                "status": "ok"
            })
        except Exception as e:
            elapsed = time.time() - q_start
            print(f"  ERRO após {elapsed:.2f}s: {e}")
            results.append({
                "query": query,
                "intent": intent,
                "time_seconds": round(elapsed, 3),
                "num_citations": 0,
                "context_length": 0,
                "status": f"error: {str(e)[:100]}"
            })

        print()

    total_elapsed = time.time() - total_start
    ok_count = sum(1 for r in results if r["status"] == "ok")
    error_count = sum(1 for r in results if r["status"] != "ok")
    avg_time = sum(r["time_seconds"] for r in results) / len(results) if results else 0

    print(f"{'='*80}")
    print(f"RESULTADOS FINAIS")
    print(f"{'='*80}")
    print(f"Total: {len(results)} queries")
    print(f"Sucesso: {ok_count}")
    print(f"Erros: {error_count}")
    print(f"Tempo total: {total_elapsed:.2f}s")
    print(f"Tempo médio por query: {avg_time:.2f}s")
    print(f"Tempo médio (sucesso): {sum(r['time_seconds'] for r in results if r['status'] == 'ok') / max(ok_count, 1):.2f}s")
    print()

    slow_queries = [r for r in results if r["time_seconds"] > 3.0]
    if slow_queries:
        print("⚠️  QUERIES LENTAS (>3s):")
        for r in slow_queries:
            print(f"  - {r['query'][:60]}... ({r['time_seconds']:.2f}s)")
    else:
        print("✅ Nenhuma query lenta detectada.")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries": len(results),
        "success": ok_count,
        "errors": error_count,
        "total_time_seconds": round(total_elapsed, 2),
        "avg_time_seconds": round(avg_time, 3),
        "slow_queries_count": len(slow_queries),
        "results": results
    }

    report_path = os.path.join(os.path.dirname(__file__), "stress_test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nRelatório salvo em: {report_path}")

    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_stress_test()
