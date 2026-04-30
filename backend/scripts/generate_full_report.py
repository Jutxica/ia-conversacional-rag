import os
import json
from supabase import create_client
from dotenv import load_dotenv
from collections import Counter

load_dotenv('backend/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

def generate_report():
    print("="*50)
    print("RELATÓRIO DE INDEXAÇÃO - DEHON AI")
    print("="*50)
    
    try:
        # Busca o total exato e os metadados (usando contagem exata do banco)
        res_count = supabase.table('documents').select('id', count='exact').limit(1).execute()
        total_real = res_count.count
        
        # Busca amostra de metadados para as porcentagens (limitado a 5000 para performance)
        res = supabase.table('documents').select('metadata').limit(5000).execute()
        
        if not res.data:
            print("O banco de dados está vazio.")
            return

        siglas = []
        for doc in res.data:
            meta = doc.get('metadata', {})
            if isinstance(meta, str):
                meta = json.loads(meta)
            siglas.append(meta.get('sigla', 'SEM_SIGLA'))

        counts = Counter(siglas)
        total = sum(counts.values())

        print(f"{'SIGLA':<15} | {'TRECHOS':<10} | {'PORCENTAGEM':<10}")
        print("-" * 45)
        
        for sigla, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total) * 100
            print(f"{sigla:<15} | {count:<10} | {pct:>9.2f}%")
            
        print("-" * 45)
        print(f"{'AMOSTRA (STATS)':<15} | {total:<10} | 100.00%")
        print(f"{'TOTAL NO BANCO':<15} | {total_real:<10}")
        print("="*50)

    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")

if __name__ == "__main__":
    generate_report()
