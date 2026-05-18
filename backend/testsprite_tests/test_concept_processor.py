import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from rag.concept_processor import processor


def test_expand_query_reparacao():
    result = processor.expand_query("Explique a reparação")
    assert "reparação" in result.lower() or "oblação" in result.lower()


def test_expand_query_no_match():
    result = processor.expand_query("Qual a capital da França?")
    assert result == "Qual a capital da França?"


def test_get_concept_context_reparacao():
    result = processor.get_concept_context("reparacao")
    assert "Contexto" in result or "reparacao" in result.lower()


def test_get_concept_context_no_match():
    result = processor.get_concept_context("matemática")
    assert result == ""


def test_expand_query_coracao_jesus():
    result = processor.expand_query("Fale sobre o Sagrado Coração")
    assert len(result) > len("Fale sobre o Sagrado Coração")


def test_expand_query_empty():
    result = processor.expand_query("")
    assert result == ""
