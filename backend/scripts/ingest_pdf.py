import os
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from firecrawl import FirecrawlApp
from langchain_text_splitters import MarkdownTextSplitter

# Configuração de Logging Profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configurações via Variáveis de Ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    logger.error("Variáveis de ambiente críticas ausentes (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY)!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# FirecrawlApp requires FIRECRAWL_API_KEY in environment or passed directly
if FIRECRAWL_API_KEY:
    firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
else:
    # Will try to look up FIRECRAWL_API_KEY from environment internally
    firecrawl_app = FirecrawlApp()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings em lote (2000 dimensões para text-embedding-3-large)."""
    # Limite seguro de tamanho em caracteres caso algo fique muito grande
    cleaned_texts = [t[:30000].replace("\n", " ") for t in texts] 
    response = client_openai.embeddings.create(
        input=cleaned_texts, 
        model="text-embedding-3-large",
        dimensions=2000 # Limite máximo suportado pelo índice HNSW no pgvector neste schema
    )
    return [d.embedding for d in response.data]

def ingest_pdf(file_path: str, sigla: str = "PDF", document_weight: int = 5, title: str = None):
    logger.info(f"Processando PDF: {os.path.basename(file_path)}")
    
    if not title:
        title = os.path.splitext(os.path.basename(file_path))[0]
    
    # Extrai markdown usando Firecrawl parse v2
    try:
        logger.info("Enviando PDF para o Firecrawl parse...")
        document = firecrawl_app.parse(file=file_path)
        markdown_text = document.markdown
        if not markdown_text:
            logger.warning(f"O documento parseado não retornou markdown: {file_path}")
            return
        logger.info(f"PDF parseado com sucesso. Tamanho do markdown: {len(markdown_text)} caracteres.")
    except Exception as e:
        logger.error(f"Erro ao parsear PDF com Firecrawl: {e}")
        return

    # Dividir o markdown em chunks
    logger.info("Dividindo o texto em chunks...")
    splitter = MarkdownTextSplitter(chunk_size=3000, chunk_overlap=300)
    texts = splitter.split_text(markdown_text)
    
    chunks_data = []
    
    for idx, chunk_text in enumerate(texts):
        chunks_data.append({
            "content": chunk_text,
            "metadata": {
                "title": title,
                "sigla": sigla,
                "document_weight": document_weight,
                "source_id": os.path.basename(file_path),
                "chunk_index": idx,
                # Outros metadados compatíveis com a tabela existente
                "entities": {"people": [], "places": [], "concepts": []},
                "receivers": [],
                "destinatario": None,
                "par_range": [0, 0]
            }
        })
        
    logger.info(f"PDF dividido em {len(chunks_data)} chunks.")

    # Ingestão no Supabase com Embedding Batching
    batch_size = 50
    total_inserted = 0
    for i in range(0, len(chunks_data), batch_size):
        batch = chunks_data[i:i + batch_size]
        try:
            # Pede embeddings para todos os conteúdos do lote
            embeddings = get_embeddings_batch([c["content"] for c in batch])
            for j, emb in enumerate(embeddings):
                batch[j]["embedding"] = emb
            
            # Insere no supabase
            response = supabase.table("documents").insert(batch).execute()
            total_inserted += len(response.data)
            logger.info(f"Inseridos {total_inserted}/{len(chunks_data)} chunks...")
        except Exception as e:
            logger.error(f"Erro no lote do arquivo {file_path}: {e}")

    logger.info(f"Ingestão concluída para {file_path}!")

def main():
    parser = argparse.ArgumentParser(description="Ingestão de PDF para RAG usando Firecrawl")
    parser.add_argument("file_path", help="Caminho para o arquivo PDF local")
    parser.add_argument("--sigla", default="PDF", help="Sigla do documento (ex: DOC, PDF)")
    parser.add_argument("--weight", type=int, default=5, help="Peso de busca do documento")
    parser.add_argument("--title", help="Título do documento (opcional)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        logger.error(f"Arquivo não encontrado: {args.file_path}")
        return
        
    ingest_pdf(args.file_path, sigla=args.sigla, document_weight=args.weight, title=args.title)

if __name__ == "__main__":
    main()
