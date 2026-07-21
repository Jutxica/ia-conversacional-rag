import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega ambiente
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent))
from src.rag.gemini_client import (
    analyze_text_entities_and_sentiment_gemini,
    generate_gemini_stream
)

def run_tests():
    print("--- INICIANDO TESTE DO CLIENTE GEMINI / NLU ---")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("ERRO: GEMINI_API_KEY não encontrada no seu arquivo .env!")
        return

    print(f"Chave encontrada: {GEMINI_API_KEY[:8]}...{GEMINI_API_KEY[-4:]}")

    # Teste 1: Testar NLU de entidades
    sample_text = (
        "Em 17 de julho de 1878, Padre Leão Dehon fundou a Congregação dos Sacerdotes do Sagrado Coração de Jesus "
        "na cidade de Saint-Quentin, na França, para propagar a oblação de amor. Ele escreveu muitas cartas para a "
        "Irmã Maria de Jesus relatando suas aflições espirituais."
    )

    print("\n--- TESTE 1: Analisando Entidades e Sentimento ---")
    try:
        nlu_result = analyze_text_entities_and_sentiment_gemini(sample_text)
        import json
        print(json.dumps(nlu_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Falha no teste NLU: {e}")

    # Teste 2: Testar Chat Streaming
    print("\n--- TESTE 2: Chat Streaming com Gemini ---")
    prompt = "Quem foi o Padre Leão Dehon? Responda em apenas um parágrafo."
    try:
        stream = generate_gemini_stream(
            prompt=prompt,
            system_instruction="Você é o Dehon AI, responda de forma curta e direta."
        )
        for token in stream:
            print(token, end="", flush=True)
        print()
    except Exception as e:
        print(f"Falha no teste de Chat: {e}")

    print("\n--- TESTES CONCLUÍDOS ---")

if __name__ == "__main__":
    run_tests()
