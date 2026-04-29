import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('backend/.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

def check_db():
    print("--- Verificação de Banco de Dados ---")
    try:
        # 1. Contagem total
        res = supabase.table('documents').select('id', count='exact').limit(1).execute()
        print(f"Total de documentos na tabela: {res.count}")
        
        # 2. Amostra de metadados
        sample = supabase.table('documents').select('metadata').limit(5).execute()
        if sample.data:
            print("\nAmostra de Metadados encontrados:")
            for i, d in enumerate(sample.data):
                print(f"{i+1}: {d['metadata']}")
        else:
            print("\nNenhum documento encontrado na tabela.")
            
        # 3. Verificar especificamente por cartas (COR ou 1LD)
        letters = supabase.table('documents').select('id').ilike('content', '%carta%').limit(1).execute()
        print(f"\nBusca por palavra 'carta' retornou documentos? {'Sim' if letters.data else 'Não'}")

    except Exception as e:
        print(f"Erro ao acessar banco: {e}")

if __name__ == "__main__":
    check_db()
