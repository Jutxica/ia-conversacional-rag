# Roadmap Dehon AI - Próximos 15 Dias

Este documento marca as prioridades absolutas para a evolução do sistema RAG após a migração bem-sucedida para Supabase e indexação do corpus total.

## 🎯 Objetivo Principal
Elevar a confiança do sistema para 95%+ e garantir precisão acadêmica cirúrgica.

---

## 🗓️ Semana 2: Inteligência de Busca e Re-ranking

### 1. Cross-Encoder Re-ranker
- **O que é:** Um segundo modelo de IA que re-classifica os 20 melhores resultados da busca híbrida.
- **Implementação:** Integrar `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Impacto:** Eliminação de alucinações baseadas em fragmentos irrelevantes.

### 2. Query Intent (Detecção de Intenção)
- **O que é:** Classificar a pergunta do usuário antes de buscar no banco.
- **Categorias:**
    - `HISTORICAL`: Datas, locais, eventos.
    - `THEOLOGICAL`: Conceitos, reflexões, espiritualidade.
    - `CITATION`: Busca por obras ou siglas específicas.
- **Impacto:** Ajuste dinâmico dos parâmetros de busca (Alpha) para cada tipo de pergunta.

### 3. Dynamic Confidence Score
- **O que é:** Um cálculo de confiança baseado na probabilidade real retornada pelo Re-ranker.
- **Impacto:** Transparência total para o pesquisador sobre a confiabilidade da citação.

---

## ✅ Consolidação Atual (Semana 1)
- [x] Migração para Supabase.
- [x] Indexação de ~5.100 fragmentos (Corpus Híbrido).
- [x] Implementação de Busca Híbrida (Vector + Keyword).
- [x] Chunking com sobreposição (5 parágrafos + 1 overlap).
- [x] Threshold dinâmico (Cartas: 80 chars | Outros: 200 chars).

---
*Documento gerado em 28/04/2026 para acompanhamento do projeto.*
