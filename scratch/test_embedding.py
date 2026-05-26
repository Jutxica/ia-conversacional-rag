import sys
import os

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
    print("Tiktoken importado com sucesso!")
except Exception as e:
    print(f"Erro ao importar tiktoken: {e}")
    tokenizer = None

def _truncate_text(text: str, max_tokens: int = 8000) -> str:
    try:
        if tokenizer:
            tokens = tokenizer.encode(text)
            print(f"Texto original: {len(text)} chars, {len(tokens)} tokens.")
            if len(tokens) > max_tokens:
                truncated = tokenizer.decode(tokens[:max_tokens])
                print(f"Truncado com tiktoken para {len(truncated)} chars, {len(tokenizer.encode(truncated))} tokens.")
                return truncated
    except Exception as e:
        print(f"Erro no truncamento tiktoken: {e}")
    
    # Fallback
    approx = text[:max_tokens * 3]
    print(f"Fallback usado. Aprox: {len(approx)} chars.")
    return approx

# Teste com uma string gigante (repetição de caracteres com acentos)
large_text = "Esta é uma frase de teste com acentuação e caracteres especiais para simular português. " * 300
print(f"Tamanho do texto gigante: {len(large_text)} chars.")
res = _truncate_text(large_text, max_tokens=100)
print(f"Resultado final: {len(res)} chars.")
