import os
import json
import re
import time
import argparse
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

# Configurações
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_text(text):
    """Remove metadados técnicos, datas ISO e ruídos do texto."""
    if not text: return ""
    text = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '', text)
    text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '', text)
    text = re.sub(r'DehonDocs.*?\n', '', text)
    return text.strip()

def get_embedding(text):
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def ingest_file(file_path):
    print(f"Processando: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extrai o corpo do texto e metadados críticos
    content_obj = data.get('content', {})
    full_text = content_obj.get('text', '') if isinstance(content_obj, dict) else (content_obj or "")
    
    # FUSÃO DE METADADOS: Para cartas, o destinatário e o resumo são cruciais
    ps = data.get('prosearch', {})
    receivers = ", ".join(ps.get('receivers', []))
    summary = ps.get('content', '')
    title = data.get('title') or ps.get('title') or ''
    
    # Criamos um "Texto Enriquecido" para indexação
    enriched_text = f"TÍTULO: {title}\nDESTINATÁRIO: {receivers}\nRESUMO: {summary}\n\nCONTEÚDO:\n{full_text}"
    
    paragraphs = [p.strip() for p in enriched_text.split('\n') if p.strip()]
    
    chunks_to_insert = []
    
    # ESTRATÉGIA DE JANELA DE PROVA (Context Expansion)
    # Janela de 12 parágrafos (~1000 tokens) com overlap de 3
    window_size = 12
    overlap = 3
    chunk_index = 0
    source_id = os.path.basename(file_path)
    
    for i in range(0, len(paragraphs), window_size - overlap):
        window = paragraphs[i:i + window_size]
        chunk_text = clean_text(" ".join(window))
        
        # Como aumentamos a janela, o threshold mínimo também sobe para garantir densidade
        # Cartas (COR) aceitam 200, outros 500.
        threshold = 200 if source_id.startswith("COR-") else 500
        
        # AJUSTE: Se o documento for menor que o threshold, mas for o ÚNICO chunk, 
        # nós o mantemos para não perder informação valiosa (especialmente cartas).
        if len(chunk_text) < threshold and len(paragraphs) > window_size:
            continue
            
        embedding = get_embedding(chunk_text)
        
        # Prepara metadados robustos para Contextual Retrieval
        ps = data.get('prosearch', {})
        metadata = {
            "title": data.get('title') or ps.get('title') or 'Sem Título',
            "author": data.get('author') or (ps.get('authors')[0] if ps.get('authors') else None) or 'Pe. Dehon',
            "sigla": data.get('sigla') or (ps.get('dehonquote', '').split()[0] if ps.get('dehonquote') else None) or 'OUTROS',
            "dehonquote": data.get('dehonquote') or ps.get('dehonquote', ''),
            "document_name": source_id,
            "source_id": source_id,
            "chunk_index": chunk_index,
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        chunks_to_insert.append({
            "content": chunk_text,
            "metadata": metadata,
            "embedding": embedding
        })
        
        chunk_index += 1
        
        if len(chunks_to_insert) >= 10: # Batch menor para blocos maiores
            supabase.table("documents").insert(chunks_to_insert).execute()
            chunks_to_insert = []
            print(f"Inseridos 10 blocos de {data.get('sigla')} (Janela de Prova index {chunk_index})...")

    # Insere o restante
    if chunks_to_insert:
        supabase.table("documents").insert(chunks_to_insert).execute()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", help="Filtra por sigla (ex: 1LD)")
    args = parser.parse_args()

    corpus_dir = "C:/Users/jutxi/OneDrive/Desktop/OpenSquad/squads/ia-conversacional-rag/backend/data/dehon_corpus"
    
    count = 0
    for root, dirs, files in os.walk(corpus_dir):
        for file in files:
            if not file.endswith('.json'): continue
            
            file_path = os.path.join(root, file)
            try:
                # Abrimos apenas o cabeçalho para checar a sigla antes de processar pesado
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                ps = data.get('prosearch', {})
                sigla = data.get('sigla') or (ps.get('dehonquote', '').split()[0] if ps.get('dehonquote') else None) or 'OUTROS'
                name = data.get('name', '')
                
                if args.filter and (args.filter not in sigla and args.filter not in name):
                    continue

                ingest_file(file_path)
                count += 1
            except Exception as e:
                print(f"Erro ao processar {file}: {e}")

    print(f"Processamento concluído. {count} documentos integrados ao Supabase.")

if __name__ == "__main__":
    main()