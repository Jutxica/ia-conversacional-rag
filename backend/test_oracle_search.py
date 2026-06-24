from src.rag.oracle_search import oracle_search_context
import os

print("Testing Oracle Search...")
os.environ["ORACLE_DB_PASSWORD"] = "Mualilissa_2026!"

result = oracle_search_context("amor ao coração de jesus", top_k=2)
print("Contexto:")
print(result["context"])
print("Citações:")
print(result["citations"])
