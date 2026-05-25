import sys
import os
import pytest
from unittest.mock import MagicMock

# Adiciona o diretório src e o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from main import _get_scope_filter, condense_query
import main

def test_get_scope_filter_legacy_scopes():
    # Geral deve retornar None
    assert _get_scope_filter("Geral") is None
    
    # Mapeamento de Espiritualidade
    esp_siglas = _get_scope_filter("Espiritualidade")
    assert esp_siglas is not None
    assert "ASC" in esp_siglas  # ASC is Obras Espirituais
    assert "CSC" not in esp_siglas  # CSC is Obras Sociais

    # Mapeamento de Social
    soc_siglas = _get_scope_filter("Social")
    assert soc_siglas is not None
    assert "CSC" in soc_siglas
    assert "ASC" not in soc_siglas

def test_get_scope_filter_friendly_scopes():
    # Espiritualidade e Retiros
    esp_siglas = _get_scope_filter("Espiritualidade e Retiros")
    assert esp_siglas is not None
    assert "ASC" in esp_siglas
    
    # Social e Político
    soc_siglas = _get_scope_filter("Social e Político")
    assert soc_siglas is not None
    assert "CSC" in soc_siglas

    # Vida e Biografia
    bio_siglas = _get_scope_filter("Vida e Biografia")
    assert bio_siglas is not None
    assert "NHV" in bio_siglas  # NHV is Diários

    # Correspondência
    cor_siglas = _get_scope_filter("Correspondência")
    assert cor_siglas is not None
    assert "1LD" in cor_siglas  # 1LD is Correspondência

def test_get_scope_filter_custom_categories():
    # Filtro direto por categorias
    categories = ["Obras Espirituais", "Obras Sociais"]
    custom_siglas = _get_scope_filter(None, categories=categories)
    assert "ASC" in custom_siglas
    assert "CSC" in custom_siglas
    assert "NHV" not in custom_siglas

    # Filtro 'Inéditos e Outros' expandido
    custom_siglas_ineditos = _get_scope_filter(None, categories=["Inéditos e Outros"])
    assert "ACD" in custom_siglas_ineditos  # ACD is Inéditos
    assert "CFL" in custom_siglas_ineditos  # CFL is Obras Diversas
    assert "CHR" in custom_siglas_ineditos  # CHR is Artigos
    assert "ASC" not in custom_siglas_ineditos

def test_condense_query_empty_history():
    # Sem histórico, retorna original
    assert condense_query("Quem foi Padre Dehon?", []) == "Quem foi Padre Dehon?"

def test_condense_query_with_history(monkeypatch):
    # Mock do cliente OpenAI
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content="Quando o Padre Dehon nasceu?"))
    ]
    mock_client.chat.completions.create.return_value = mock_completion
    
    # Substitui o cliente global no main
    monkeypatch.setattr(main, "client", mock_client)
    
    history = [
        {"role": "user", "content": "Quem foi Padre Dehon?"},
        {"role": "assistant", "content": "Ele foi o fundador dos Sacerdotes do Sagrado Coração."}
    ]
    
    result = condense_query("Quando ele nasceu?", history)
    assert result == "Quando o Padre Dehon nasceu?"
    
    # Verifica se chamou a criação do completion com o prompt correto
    assert mock_client.chat.completions.create.called
