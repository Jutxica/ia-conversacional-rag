import os
import sys
import re
import time
import json
import array
import argparse
import tempfile
import io
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da pasta backend
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.oracle_db_client import get_oracle_connection
from src.google_document_ai import extract_text_from_pdf, setup_google_credentials
from openai import OpenAI

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

print("--- INICIADOR DE SINCRONIZAÇÃO GOOGLE DRIVE -> ORACLE DATABASE ---", flush=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

if not OPENAI_API_KEY:
    print("ERRO: OPENAI_API_KEY não encontrada no ambiente.", flush=True)
    sys.exit(1)

if not GOOGLE_DRIVE_FOLDER_ID:
    print("ERRO: GOOGLE_DRIVE_FOLDER_ID não configurado no ambiente.", flush=True)
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
        dimensions=1536
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

def get_drive_service():
    setup_google_credentials()
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise ValueError("Credenciais do Google Cloud (GOOGLE_APPLICATION_CREDENTIALS) não encontradas.")
        
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def download_file_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    file_bytes = io.BytesIO()
    downloader = MediaIoBaseDownload(file_bytes, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return file_bytes.getvalue()

def process_and_ingest_file(filename, file_content, conn):
    cursor = conn.cursor()
    
    # Verificar se já existe no Oracle
    cursor.execute("SELECT count(*) FROM documents WHERE JSON_VALUE(metadata, '$.source_id') = :source_id", source_id=filename)
    if cursor.fetchone()[0] > 0:
        print(f">>> Pulando {filename} (já existe no Oracle Database).", flush=True)
        return False

    print(f"\n>>> Processando PDF: {filename} ({len(file_content) / (1024*1024):.2f} MB)", flush=True)
    
    # Extrair texto (com Document AI OCR se ativado, ou fallback PyPDF)
    full_text = extract_text_from_pdf(file_content)
    if not full_text or len(full_text.strip()) < 100:
        print(f"  [ERRO] Texto extraído do PDF {filename} é inválido ou curto demais.", flush=True)
        return False

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
            if "insufficient_quota" in str(e).lower():
                print("\n[ERRO CRÍTICO] A cota da sua API Key da OpenAI acabou (insufficient_quota).", flush=True)
                conn.commit()
                sys.exit(1)
            time.sleep(1)
            
    conn.commit()
    print(f"  [CONCLUÍDO] {filename} carregado no Oracle com {chunk_index} chunks.", flush=True)
    return True

def sync_drive():
    print(f"Conectando ao Oracle Database...")
    conn = get_oracle_connection()
    if not conn:
        print("ERRO: Não foi possível conectar ao banco Oracle.", flush=True)
        return {"status": "error", "error": "Database connection failed"}
        
    try:
        print(f"Autenticando com o Google Drive...")
        service = get_drive_service()
        
        print(f"Buscando PDFs na pasta ID: {GOOGLE_DRIVE_FOLDER_ID}...")
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, pageSize=100, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        print(f"Total de PDFs encontrados no Drive: {len(files)}", flush=True)
        
        synced_count = 0
        skipped_count = 0
        
        for i, file_item in enumerate(files):
            file_id = file_item['id']
            filename = file_item['name']
            
            # Verificar se já existe antes de baixar (economiza banda)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM documents WHERE JSON_VALUE(metadata, '$.source_id') = :source_id", source_id=filename)
            if cursor.fetchone()[0] > 0:
                skipped_count += 1
                continue
                
            print(f"\n--- Progresso: {i+1}/{len(files)} ---", flush=True)
            print(f"Baixando {filename} do Drive...", flush=True)
            file_content = download_file_from_drive(service, file_id)
            
            success = process_and_ingest_file(filename, file_content, conn)
            if success:
                synced_count += 1
                
        conn.close()
        print(f"\nSincronização concluída! Inseridos: {synced_count}, Pulados: {skipped_count}", flush=True)
        return {"status": "success", "synced": synced_count, "skipped": skipped_count}
    except Exception as e:
        if conn:
            conn.close()
        print(f"ERRO durante a sincronização: {e}", flush=True)
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    sync_drive()
