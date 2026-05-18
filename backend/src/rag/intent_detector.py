import os
import re
import json
from typing import Dict, Any

class IntentDetector:
    def __init__(self):
        self.concepts = {}
        self.authority_themes = {}
        self.load_data()

    def load_data(self):
        base = os.path.dirname(__file__)
        concepts_path = os.path.join(base, 'conceitos.json')
        themes_path = os.path.join(base, 'autoridade_tematica.json')

        if os.path.exists(concepts_path):
            try:
                with open(concepts_path, 'r', encoding='utf-8') as f:
                    self.concepts = json.load(f)
            except Exception as e:
                print(f"[INTENT] Erro ao carregar conceitos: {e}")

        if os.path.exists(themes_path):
            try:
                with open(themes_path, 'r', encoding='utf-8') as f:
                    self.authority_themes = json.load(f)
            except Exception as e:
                print(f"[INTENT] Erro ao carregar temas: {e}")

    def detect(self, query: str) -> Dict[str, Any]:
        scores = {
            "HISTORICAL": 0.0,
            "THEOLOGICAL": 0.0,
            "CITATION": 0.0,
            "GENERAL": 0.1
        }
        q = query.lower().strip()

        # --- HISTORICAL Patterns ---
        historical_patterns = {
            "dates": [
                r'\b\d{4}\b', r'\bséc\.?\s*(xix|xx|xviii)\b', r'\bséculo\s*(xix|xx|xviii)\b',
                r'\b18\d{2}\b', r'\b19\d{2}\b', r'\b17\d{2}\b',
                r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b',
                r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b'
            ],
            "locations": [
                r'\broma\b', r'\bfrança\b', r'\france\b', r'\bbrasil\b', r'\bbélgica\b',
                r'\bparis\b', r'\bla louvière\b', r'\blouvre\b', r'\bstrasburgo\b',
                r'\balsácia\b', r'\balsace\b', r'\blille\b', r'\bsoissons\b',
                r'\bhaut-rhin\b', r'\b(américa|europa|África)\b.*\bsul\b',
                r'\bcidade\b', r'\bpaís\b', r'\bestado\b', r'\bregião\b', r'\bprovíncia\b'
            ],
            "biographical": [
                r'\bnasceu\b', r'\bmorreu\b', r'\bfaleceu\b', r'\bnascimento\b', r'\bmorte\b',
                r'\bfundou\b', r'\bcriou\b', r'\bestabeleceu\b',
                r'\bprimeira.*guerra\b', r'\bsegunda.*guerra\b', r'\bguerra.*mundial\b',
                r'\bcongregação\b', r'\bfundação\b', r'\borigem\b', r'\bhistória\b',
                r'\bdata\b', r'\bano\b', r'\bépoca\b', r'\bperíodo\b',
                r'\bviajou\b', r'\bviagem\b', r'\breunião\b', r'\bencontro\b',
                r'\bvisitou\b', r'\besteve\b', r'\bfoi\b.*\b(para|a)\b',
                r'\bbiógrafo\b', r'\bbiography\b', r'\bbiographie\b',
                r'\bquem\b', r'\bquem foi\b', r'\bquem é\b'
            ]
        }

        for category, patterns in historical_patterns.items():
            for pat in patterns:
                if re.search(pat, q):
                    scores["HISTORICAL"] += 0.12

        # --- THEOLOGICAL Patterns ---
        theological_patterns = [
            r'\breparação\b', r'\boblação\b', r'\bimolação\b',
            r'\bsagrado coração\b', r'\bcoração de jesus\b',
            r'\bespiritualidade\b', r'\bmística\b', r'\boração\b',
            r'\bdoutrina\b', r'\bteologia\b', r'\bteológico\b',
            r'\bjustiça social\b', r'\bdoutrina social\b',
            r'\bencíclica\b', r'\b(rerum|novarum|quadragesimo|anno)\b',
            r'\bbem-aventurança\b', r'\beucaristia\b', r'\bsacerdócio\b',
            r'\bvirtude\b', r'\bpecado\b', r'\bgraça\b', r'\bredenção\b',
            r'\bpobreza\b', r'\bobediência\b', r'\bcastidade\b',
            r'\bconsagração\b', r'\bdevoção\b', r'\bculto\b',
            r'\bamor oblativo\b', r'\bamor de deus\b',
            r'\bespírito de vítima\b', r'\boferecimento\b'
        ]

        for pat in theological_patterns:
            if re.search(pat, q):
                scores["THEOLOGICAL"] += 0.10

        # Check concept triggers for theological boost
        for key, data in self.concepts.items():
            if key.startswith("_"):
                continue
            all_triggers = [key] + data.get("sinonimo", [])
            for trigger in all_triggers:
                if trigger.lower() in q:
                    scores["THEOLOGICAL"] += 0.08
                    break

        # Check authority themes for theological boost
        for theme_name, theme_data in self.authority_themes.items():
            triggers = theme_data.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in q:
                    scores["THEOLOGICAL"] += 0.06
                    break

        # --- CITATION Patterns ---
        citation_patterns = [
            r'\b(asc|con|doc|cor|art)\b', r'\b(1ld|lc1|lc2|lcc|1lc|1lc1)\b',
            r'\b(nhv|rso|dju|ext|mis|nqt|ntd|nto|acd|dis)\b',
            r'\b(rev|drd|ent|qss|cfl|ret|apd|dss|exc|chr)\b',
            r'\b(pri|rmp|pdr|smj|mmr|rsc|psc|svn|dsp|ecd)\b',
            r'\b(adp|arp|mso|mla|ncg)\b',
            r'\bsigla\b', r'\bcitação\b', r'\breferência\b', r'\bfonte\b',
            r'\bobra\b', r'\bdocumento\b', r'\bcarta\b',
            r'\bdehoniana\b', r'\bdehoniano\b',
            r'\bprocur[ao]\b.*\b(sigla|código|referência)\b',
            r'\bqual\b.*\bsigla\b', r'\bcomo citar\b'
        ]
        for pat in citation_patterns:
            if re.search(pat, q):
                scores["CITATION"] += 0.12

        # --- Multi-word penalties to avoid false positives ---
        word_count = len(q.split())
        if word_count > 15:
            scores["CITATION"] *= 0.5
        if word_count < 3:
            scores["HISTORICAL"] *= 0.7
            scores["THEOLOGICAL"] *= 0.7

        # --- Contextual disambiguation ---
        comparative_words = ['comparação', 'comparar', 'diferença', 'vs', 'versus', 'evolução', 'mudança']
        has_comparative = any(w in q for w in comparative_words)
        if has_comparative:
            scores["HISTORICAL"] += 0.15

        # Normalize so the dominant intent stands out
        max_score = max(scores.values())
        if max_score > 0:
            factor = 1.0 / max_score
            for k in scores:
                scores[k] = round(scores[k] * factor * 0.9, 4)

        intent = max(scores, key=scores.get)
        confidence = scores[intent]

        threshold = 0.3
        if confidence < threshold:
            intent = "GENERAL"
            confidence = 0.5

        return {
            "intent": intent,
            "confidence": round(confidence, 2),
            "scores": scores
        }

detector = IntentDetector()
