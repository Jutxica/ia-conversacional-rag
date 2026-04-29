# Fase 4: RAG System Design

## 📋 Objetivo
Arquitetar o sistema de Retrieval-Augmented Generation (RAG) com retrieval, reranking, citation tracking e quality assurance.

## 🎯 Deliverables

### D4.1 RAG Architecture Document
- [ ] Componentes do pipeline RAG
- [ ] Fluxo detalhado: embedding → search → rerank → augment
- [ ] Decision matrix para cada componente

### D4.2 Data Chunking Strategy
- [ ] Algoritmo de divisão de documentos
- [ ] Tamanho ótimo de chunks
- [ ] Overlap strategy
- [ ] Metadata extraction

### D4.3 Embedding Model Selection
- [ ] Comparação de modelos
- [ ] Dimensionalidade (256, 384, 1536?)
- [ ] Cost vs. quality trade-off

### D4.4 Citation Tracking System
- [ ] Mapping chunk → original document
- [ ] Citation metadata schema
- [ ] Output format (URL, excerpt, page number)

### D4.5 RAG Query Engine Code Skeleton
- [ ] Vector search implementation
- [ ] Reranker integration
- [ ] Prompt augmentation logic

## 🔍 RAG Pipeline

```
User Query
    │
    ├─ Embed query (OpenAI embeddings API)
    │
    ├─ Vector search (Pinecone)
    │   └─ Return top-100 dense matches + metadata
    │
    ├─ BM25 search (sparse, lexical)
    │   └─ Return top-50 sparse matches
    │
    ├─ Hybrid reranking (combine dense + sparse)
    │   └─ Keep top-20 results
    │
    ├─ Cross-encoder reranking (LLM-based)
    │   └─ Keep top-5 results
    │
    ├─ Augment system prompt with context
    │   ├─ Original system prompt
    │   ├─ Top-5 documents (with citations)
    │   └─ User query + conversation history
    │
    ├─ Call LLM with augmented prompt
    │
    └─ Return response + citations
```

## 📄 Data Chunking Strategy

### Chunk Size Analysis

| Size | Pros | Cons |
|------|------|------|
| 128 tokens | High granularity, precise retrieval | Many overlaps, fragmented meaning |
| 256 tokens | Good balance | Standard, perhaps generic |
| 512 tokens | Semantic coherence | Possible redundancy |
| 1024 tokens | Full context | May miss relevant small pieces |

**Recommendation:** 512 tokens (~ 2,000-3,000 characters) with 50-token overlap

### Chunking Algorithm

```python
def chunk_document(text: str, chunk_size: int = 512, overlap: int = 50):
    """
    Split document into overlapping chunks maintaining semantic boundaries.
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = count_tokens(sentence)
        
        if current_size + sentence_size > chunk_size:
            # Save chunk and start new with overlap
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap_sentences:] + [sentence]
            current_size = sum(count_tokens(s) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
```

## 🧮 Embedding Model Selection

**OpenAI text-embedding-3-large**
- Dimensionality: 1536
- Cost: $0.13 per 1M tokens
- Quality: Excellent, SOtA
- Pro: Best quality, trusted
- Con: Expensive, vendor lock-in

**Sentence-Transformers (open-source)**
- Dimensionality: 384-768
- Cost: $0 (self-hosted)
- Quality: Good, suitable for domain-specific fine-tuning
- Pro: Free, can fine-tune
- Con: Setup overhead, slightly lower quality

**Recommendation:** OpenAI 3-large for production, maintain option for Sentence-Transformers for cost optimization

## 🎯 Reranking Strategy

### Stage 1: Hybrid Scoring

```
Score = 0.7 * dense_score + 0.3 * sparse_score
```

Keep top-20 results

### Stage 2: Cross-Encoder Reranking

```
For each of top-20:
  score = cross_encoder("query", "candidate", "context")
Keep top-5
```

### Cross-Encoder Implementation

```python
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
    
    async def rerank(
        self, 
        query: str, 
        candidates: List[str], 
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        scores = self.model.predict([(query, cand) for cand in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
```

## 📍 Citation Tracking

### Metadata Schema

```json
{
  "chunk_id": "doc_001_chunk_05",
  "document_id": "doc_001",
  "document_title": "System Architecture Guide",
  "document_url": "/documents/system-architecture-guide",
  "page_number": 3,
  "chunk_index": 5,
  "chunk_start_char": 4500,
  "chunk_end_char": 6200,
  "created_at": "2026-04-21T10:00:00Z",
  "tenant_id": "tenant_123"
}
```

### Citation Output Format

```markdown
**From:** [System Architecture Guide](/documents/system-architecture-guide) (Page 3)

> The system uses a modular architecture with clear separation of concerns...

[View full document →](/documents/system-architecture-guide#page-3)
```

### Citation Tracking Implementation

```typescript
interface RetrievedChunk {
  content: string;
  metadata: ChunkMetadata;
  relevance_score: number;
}

class CitationManager {
  formatCitation(chunk: RetrievedChunk): string {
    const { metadata, content } = chunk;
    return `
**Source:** [${metadata.document_title}](${metadata.document_url})
Page ${metadata.page_number} | Relevance: ${(chunk.relevance_score * 100).toFixed(0)}%

> ${content.substring(0, 200)}...
    `;
  }
  
  formatBibliography(chunks: RetrievedChunk[]): string {
    const unique = Array.from(
      new Map(chunks.map(c => [c.metadata.document_id, c])).values()
    );
    return unique
      .map(c => `- [${c.metadata.document_title}](${c.metadata.document_url})`)
      .join("\n");
  }
}
```

## 📊 RAG Quality Metrics

- [ ] Retrieval precision@5, @10
- [ ] MRR (Mean Reciprocal Rank)
- [ ] Citation accuracy (correct source?)
- [ ] Context relevance (is context actually used?)
- [ ] Hallucination rate (claims not supported by context?)

## ✅ Checklist de Validação

- [ ] Chunking strategy testada em exemplos reais
- [ ] Embedding model selecionado
- [ ] Reranker pipeline funcional
- [ ] Citation tracking implemented
- [ ] RAG quality benchmarks definidos
- [ ] Performance targets validados

## 📝 Notas

---

**Status:** ⏳ Aguardando design de RAG
**Próximo:** Fase 5 — Backend & Data Infrastructure
