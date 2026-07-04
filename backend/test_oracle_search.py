from dotenv import load_dotenv
load_dotenv()
import os
print("Testing Oracle Search...")
os.environ["ORACLE_DB_PASSWORD"] = "Mualilissa_2026!"
from src.rag.oracle_search import oracle_search_context

result = oracle_search_context("amor ao coração de jesus", top_k=2)
print("Contexto:")
print(result["context"])
print("Citações:")
print(result["citations"])
