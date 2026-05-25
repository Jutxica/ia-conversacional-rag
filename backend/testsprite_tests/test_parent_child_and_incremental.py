import pytest
import hashlib
import tiktoken
from main import _split_long_paragraph

def test_parent_child_splitting_logic():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # Texto representativo
    text = "Isso é um parágrafo longo de teste. " * 30
    
    # 1. Simula divisão de parent chunks
    PARENT_MAX_TOKENS = 100
    CHILD_MAX_TOKENS = 20
    
    raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    paragraphs = []
    for p in raw_paragraphs:
        paragraphs.extend(_split_long_paragraph(p, PARENT_MAX_TOKENS, tokenizer))
        
    parent_texts = []
    current_parent = []
    current_tokens = 0
    for par in paragraphs:
        par_tokens = len(tokenizer.encode(par))
        if current_tokens + par_tokens > PARENT_MAX_TOKENS and current_parent:
            parent_texts.append("\n\n".join(current_parent))
            overlap_chunk = []
            overlap_tokens = 0
            for p in reversed(current_parent):
                p_t = len(tokenizer.encode(p))
                if overlap_tokens + p_t <= 20:
                    overlap_chunk.insert(0, p)
                    overlap_tokens += p_t
                else:
                    break
            current_parent = overlap_chunk
            current_tokens = overlap_tokens
        current_parent.append(par)
        current_tokens += par_tokens
    if current_parent:
        parent_texts.append("\n\n".join(current_parent))
        
    # Verifica se os parent chunks foram gerados corretamente
    assert len(parent_texts) > 0
    
    # 2. Divide os parents em child chunks
    texts = []
    child_to_parent_map = {}
    child_index = 0
    
    for parent_text in parent_texts:
        parent_pars = [p.strip() for p in parent_text.split('\n') if p.strip()]
        child_paragraphs = []
        for p in parent_pars:
            child_paragraphs.extend(_split_long_paragraph(p, CHILD_MAX_TOKENS, tokenizer))
            
        current_child = []
        current_child_tokens = 0
        temp_children = []
        for par in child_paragraphs:
            par_tokens = len(tokenizer.encode(par))
            if current_child_tokens + par_tokens > CHILD_MAX_TOKENS and current_child:
                temp_children.append("\n\n".join(current_child))
                overlap_chunk = []
                overlap_tokens = 0
                for p in reversed(current_child):
                    p_t = len(tokenizer.encode(p))
                    if overlap_tokens + p_t <= 5:
                        overlap_chunk.insert(0, p)
                        overlap_tokens += p_t
                    else:
                        break
                current_child = overlap_chunk
                current_child_tokens = overlap_tokens
            current_child.append(par)
            current_child_tokens += par_tokens
        if current_child:
            temp_children.append("\n\n".join(current_child))
            
        for child_text in temp_children:
            texts.append(child_text)
            child_to_parent_map[child_index] = parent_text
            child_index += 1
            
    # Assegura que todos os child chunks mapeiam para o parent correspondente
    assert len(texts) > 0
    for idx, child_text in enumerate(texts):
        parent_text = child_to_parent_map[idx]
        assert child_text in parent_text
        # Cada child chunk deve ser menor que o parent correspondente
        assert len(child_text) <= len(parent_text)
