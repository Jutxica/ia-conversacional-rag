import os
from supabase import create_client
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('backend/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def inserir_manual(conteudo, sigla, titulo):
    print(f"Inserindo: {titulo} [{sigla}]...")
    
    # 1. Gerar o vetor (Embedding)
    response = client.embeddings.create(
        input=conteudo,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    
    # 2. Preparar metadados
    metadata = {
        "sigla": sigla,
        "title": titulo,
        "author": "Léon Dehon",
        "ingested_at": "manual"
    }
    
    # 3. Enviar para o Supabase
    data = {
        "content": conteudo,
        "metadata": metadata,
        "embedding": embedding
    }
    
    res = supabase.table('documents').insert(data).execute()
    print("✅ Sucesso! O documento já está disponível para consulta.")

if __name__ == "__main__":
    # EXEMPLO DE USO:
    # inserir_manual("Texto da carta...", "1LD", "Carta ao Pe. Ressel")
    print("Script pronto. Edite o final do arquivo para inserir o texto desejado.")
