import os
import sys
import re
import time
import json
import array
import argparse
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv

# Carrega .env da pasta backend
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.oracle_db_client import get_oracle_connection
from openai import OpenAI

print("--- INICIADOR DE INGESTÃO DE PDFs NO ORACLE ---", flush=True)
print(f"Caminho .env: {env_path}", flush=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORACLE_DB_PASSWORD = os.getenv("ORACLE_DB_PASSWORD", "Mualilissa_2026!")

if not OPENAI_API_KEY:
    print("ERRO: OPENAI_API_KEY não encontrada no ambiente.")
    sys.exit(1)

client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Mapeamento de siglas para títulos amigáveis
SIGLARIO = {
    "VAM": "Vida de Amor",
    "CSC": "Catecismo Social",
    "MMR": "Mês de Maria",
    "RSC": "Retiro do Sagrado Coração",
    "DSP": "Diretório Espiritual",
    "RSO": "Renovação Social Cristã",
    "NHV": "Notas sobre a História da minha Vida",
    "ASC": "O Ano com o Sagrado Coração de Jesus",
    "CSJ": "Coração Sacerdotal de Jesus",
    "CAM": "Coroas de Amor",
    "CFL": "Cadernos Falleur",
    "PDR": "Pequeno Diretório para os Reitores",
    "PSC": "Um Sacerdote do Sagrado Coração de Jesus",
    "SMJ": "Irmã Maria de Jesus",
    "SVN": "Memórias (Souvenirs)",
    "RMP": "Riqueza, Moderação ou Pobreza",
    "DIS": "Discursos e Inéditos",
    "NQT": "Nota Quotidiana"
}

def clean_text(text):
    if not text: return ""
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_openai_embedding(text):
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(
        input=[text], 
        model="text-embedding-3-large",
        dimensions=1536 # Sincronizado com a tabela Oracle (VECTOR(1536))
    ).data[0].embedding

def extract_sigla(filename):
    parts = filename.split('-')
    if len(parts) >= 2:
        return parts[1]
    return "OBRA"

def extract_recipient(text):
    first_lines = text[:500]
    match = re.search(r'(?:Ao|A|Para|Sr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', first_lines)
    if match:
        return match.group(1)
    return None

def ingest_pdf_to_oracle(file_path, conn):
    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    # Aumentado limite para 1.5GB para permitir processar as obras completas (ex: Studia Dehoniana, COR_COMPLETO)
    if file_size_mb > 1500:
        print(f">>> Pulando {filename} (tamanho {file_size_mb:.1f}MB excede o limite de 1.5GB).", flush=True)
        return

    cursor = conn.cursor()
    
    # Verificar se já existe no Oracle
    cursor.execute("SELECT count(*) FROM documents WHERE JSON_VALUE(metadata, '$.source_id') = :source_id", source_id=filename)
    if cursor.fetchone()[0] > 0:
        print(f">>> Pulando {filename} (já existe no Oracle Database).", flush=True)
        return

    print(f"\n>>> Lendo PDF: {filename} ({file_size_mb:.2f} MB)", flush=True)
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n\n"
    except Exception as e:
        print(f"  [ERRO] Falha ao extrair texto do PDF {filename}: {e}", flush=True)
        return

    paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 20]
    sigla = extract_sigla(filename)
    title = SIGLARIO.get(sigla, filename.replace('.pdf', ''))
    recipient = extract_recipient(full_text)
    
    print(f"Total de fragmentos: {len(paragraphs)}", flush=True)
    
    window_size = 12
    overlap = 3
    chunk_index = 0
    
    for i in range(0, len(paragraphs), window_size - overlap):
        window = paragraphs[i:i + window_size]
        chunk_text = clean_text(" ".join(window))
        
        if len(chunk_text) < 400 and len(paragraphs) > window_size:
            continue
            
        try:
            emb = get_openai_embedding(chunk_text)
            vec_array = array.array("f", emb)
            
            metadata = {
                "title": title,
                "author": "Pe. Dehon",
                "sigla": sigla,
                "dehonquote": f"{sigla} PDF",
                "document_name": filename,
                "source_id": filename,
                "recipient": recipient,
                "chunk_index": chunk_index,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_complete_work": True
            }
            
            cursor.execute(
                "INSERT INTO documents (content, embedding, metadata) VALUES (:content, :emb, :metadata)",
                content=chunk_text, emb=vec_array, metadata=json.dumps(metadata)
            )
            
            chunk_index += 1
            if chunk_index % 10 == 0:
                conn.commit()
                print(f"  [Inseridos] {chunk_index} blocos de {filename}...", flush=True)
                
        except Exception as e:
            print(f"  [ERRO] Falha no chunk {chunk_index} de {filename}: {e}", flush=True)
            time.sleep(1)
            
    conn.commit()
    print(f"  [CONCLUÍDO] {filename} carregado no Oracle com {chunk_index} chunks.", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Pasta com os PDFs")
    args = parser.parse_args()
    
    target_path = args.path or "/Users/fr.utxicascj/testes antigravity/ia-conversacional-rag/backend/Dehondocs"
    
    print(f"Conectando ao Oracle Database...")
    conn = get_oracle_connection()
    if not conn:
        print("ERRO: Não foi possível conectar ao banco Oracle.")
        sys.exit(1)
        
    print(f"Verificando arquivos em {target_path}...")
    
    pdf_files = []
    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            pdf_files.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.lower().endswith('.pdf') and not file.startswith('.'):
                    pdf_files.append(os.path.join(root, file))
                    
    print(f"Total de PDFs encontrados: {len(pdf_files)}")
    
    for i, file in enumerate(pdf_files):
        print(f"\n--- Progresso: {i+1}/{len(pdf_files)} ---", flush=True)
        ingest_pdf_to_oracle(file, conn)
        
    conn.close()
    print("\nProcessamento concluído com sucesso!")

if __name__ == "__main__":
    main()
