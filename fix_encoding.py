import os

file_path = 'frontend/src/index.css'

with open(file_path, 'rb') as f:
    raw_bytes = f.read()

# Tentar decodificar. O PowerShell Add-Content geralmente adiciona BOM ou UTF-16 no final.
try:
    # Como o arquivo era UTF-8 e apenas o final foi corrompido, 
    # replace vai ignorar os bytes ruins.
    text = raw_bytes.decode('utf-8', errors='replace').replace('\x00', '')
    
    # Reescrever o arquivo em UTF-8 limpo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Arquivo corrigido com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
