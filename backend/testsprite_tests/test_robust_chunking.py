import pytest
import tiktoken
from main import _split_long_paragraph, _truncate_text

def test_split_long_paragraph_standard():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # 1. Teste de texto curto (deve retornar intacto)
    text = "Isso é um parágrafo curto."
    res = _split_long_paragraph(text, 100, tokenizer)
    assert res == [text]

def test_split_long_paragraph_no_punctuation():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # 2. Teste de parágrafo gigante sem nenhuma pontuação (deve quebrar por palavras)
    huge_sentence = "palavra " * 1500 # Muito mais que 800 tokens
    res = _split_long_paragraph(huge_sentence, 800, tokenizer)
    
    # Deve quebrar em mais de uma parte
    assert len(res) > 1
    
    # Cada parte deve ser menor ou igual a 800 tokens
    for chunk in res:
        tokens = len(tokenizer.encode(chunk))
        assert tokens <= 800

def test_truncate_text_limit():
    # 3. Teste do truncamento com tiktoken ativo
    huge_text = "texto gigante para truncar " * 2000
    res = _truncate_text(huge_text, max_tokens=100)
    
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = len(tokenizer.encode(res))
    assert tokens <= 100

def test_truncate_text_fallback(monkeypatch):
    # 4. Teste do fallback caso o tokenizer seja None ou ocorra exceção
    huge_text = "português acentuado de teste " * 5000
    
    # Removemos o tiktoken do sys.modules ou fazemos o import falhar para testar o fallback
    import builtins
    real_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == 'tiktoken':
            raise ImportError("Simulated tiktoken import failure")
        return real_import(name, *args, **kwargs)
        
    monkeypatch.setattr(builtins, '__import__', mock_import)
    
    # O fallback deve limitar rigidamente os caracteres
    res = _truncate_text(huge_text, max_tokens=100)
    
    # max_tokens = 100, o limite máximo deve ser approx_limit = 200 chars
    # Como len(huge_text) > 200, ele deve ter truncado
    assert len(res) <= 200
