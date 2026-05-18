import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from rag.intent_detector import detector


def test_historical_intent():
    queries = [
        "Onde nasceu o Padre Leão Dehon?",
        "Qual ano Dehon fundou a congregação?",
        "Em que cidade Dehon morreu?",
        "Quem foi o primeiro noviço da congregação?",
        "Data da primeira guerra mundial",
    ]
    for q in queries:
        result = detector.detect(q)
        assert result["intent"] == "HISTORICAL", f"Falhou: {q} -> {result['intent']}"


def test_theological_intent():
    queries = [
        "Explique o conceito de reparação na espiritualidade",
        "O que é a oblação no pensamento dehoniano?",
        "Qual a relação entre o Sagrado Coração e a justiça social?",
        "O que significa ser uma alma vítima?",
        "Doutrina social da Igreja",
    ]
    for q in queries:
        result = detector.detect(q)
        assert result["intent"] == "THEOLOGICAL", f"Falhou: {q} -> {result['intent']}"


def test_citation_intent():
    queries = [
        "O que significa a sigla ASC?",
        "Qual é o código da obra CSC?",
        "Como citar o documento COR-1912?",
        "Referência da obra 1LD",
    ]
    for q in queries:
        result = detector.detect(q)
        assert result["intent"] == "CITATION", f"Falhou: {q} -> {result['intent']}"


def test_general_intent():
    queries = [
        "Como posso melhorar minha vida espiritual?",
        "O que você pode me dizer sobre fé?",
        "Ajude-me a entender melhor",
    ]
    for q in queries:
        result = detector.detect(q)
        assert result["intent"] == "GENERAL", f"Falhou: {q} -> {result['intent']}"


def test_intent_confidence_scores():
    result = detector.detect("Onde nasceu o Padre Leão Dehon?")
    assert "confidence" in result
    assert "scores" in result
    assert result["confidence"] > 0
    assert len(result["scores"]) == 4


def test_empty_query():
    result = detector.detect("")
    assert result["intent"] in ("GENERAL", "HISTORICAL")


def test_short_query():
    result = detector.detect("ASC")
    assert result["intent"] == "CITATION"


def test_comparative_query():
    result = detector.detect("Comparação entre reparação passiva e ativa")
    assert result["intent"] in ("HISTORICAL", "THEOLOGICAL")
