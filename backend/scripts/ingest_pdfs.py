import os
import re
import time
import argparse
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Carrega .env da pasta backend
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print(f"--- INICIANDO INGESTAO DE PDFs ---", flush=True)
print(f"Caminho .env: {env_path}", flush=True)
print(f"Supabase URL configurada: {'Sim' if os.getenv('SUPABASE_URL') else 'Nao'}", flush=True)

# Configurações
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mapeamento amigável de títulos baseado em siglas
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
    "RMP": "Riqueza, Moderação ou Pobreza"
}

def clean_text(text):
    """Limpeza básica para PDFs."""
    if not text: return ""
    # Remove números de página isolados em linhas
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove excesso de espaços e quebras
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_embedding(text):
    text = text.replace("\n", " ")
    return client_openai.embeddings.create(
        input=[text], 
        model="text-embedding-3-large",
        dimensions=2000 # Sincronizado com GraphRAG Elite 2026
    ).data[0].embedding

def extract_sigla(filename):
    """Tenta extrair a sigla do padrão OSP-VAM-0002..."""
    parts = filename.split('-')
    if len(parts) >= 2:
        return parts[1]
    return "OBRA"

def ingest_pdf(file_path):
    print(f"\n>>> Lendo PDF: {os.path.basename(file_path)}", flush=True)
    reader = PdfReader(file_path)
    
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n\n"
    
    # Divide em parágrafos (tentativa baseada em quebras duplas)
    paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 20]
    
    filename = os.path.basename(file_path)
    sigla = extract_sigla(filename)
    title = SIGLARIO.get(sigla, filename.replace('.pdf', ''))
    
    print(f"Total de fragmentos brutos: {len(paragraphs)}", flush=True)
    
    chunks_to_insert = []
    window_size = 12
    overlap = 3
    chunk_index = 0
    
    for i in range(0, len(paragraphs), window_size - overlap):
        window = paragraphs[i:i + window_size]
        chunk_text = clean_text(" ".join(window))
        
        # Threshold para obras completas (maior que cartas)
        if len(chunk_text) < 400 and len(paragraphs) > window_size:
            continue
            
        try:
            embedding = get_embedding(chunk_text)
            
            metadata = {
                "title": title,
                "author": "Pe. Dehon",
                "sigla": sigla,
                "dehonquote": f"{sigla} PDF",
                "document_name": filename,
                "source_id": filename,
                "chunk_index": chunk_index,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_complete_work": True
            }
            
            chunks_to_insert.append({
                "content": chunk_text,
                "metadata": metadata,
                "embedding": embedding
            })
            
            chunk_index += 1
            
            if len(chunks_to_insert) >= 5: # Batch pequeno para PDFs volumosos
                supabase.table("documents").insert(chunks_to_insert).execute()
                print(f"  [OK] Inseridos {len(chunks_to_insert)} blocos de {sigla}...", flush=True)
                chunks_to_insert = []
                
        except Exception as e:
            print(f"  [ERRO] Falha no chunk {chunk_index} de {filename}: {e}", flush=True)
            time.sleep(2)

    if chunks_to_insert:
        supabase.table("documents").insert(chunks_to_insert).execute()
        print(f"  [OK] Inseridos blocos finais de {sigla}.", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Caminho específico ou pasta")
    args = parser.parse_args()

    base_dir = args.path or "C:/Users/jutxi/OneDrive/Desktop/OpenSquad/squads/ia-conversacional-rag/backend/docs/Dehondocs"
    
    if os.path.isfile(base_dir):
        ingest_pdf(base_dir)
    else:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    ingest_pdf(os.path.join(root, file))

    print("\nProcessamento de PDFs concluído.", flush=True)

if __name__ == "__main__":
    main()
