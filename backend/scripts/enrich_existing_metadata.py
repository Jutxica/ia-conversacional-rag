import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Configura o path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.oracle_db_client import get_oracle_connection
from src.rag.gemini_client import analyze_text_entities_and_sentiment_gemini

# Carrega variáveis de ambiente do .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def enrich_database_metadata():
    print("--- INICIANDO ENRIQUECIMENTO RETROATIVO DE METADADOS VIA GEMINI ---")
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("[ERRO] GEMINI_API_KEY não configurada no seu arquivo .env!")
        return
        
    conn = get_oracle_connection()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco Oracle.")
        return
        
    cursor = conn.cursor()
    
    try:
        # 1. Buscar todos os nomes de documentos únicos
        print("Buscando documentos existentes no banco de dados...")
        cursor.execute("SELECT DISTINCT JSON_VALUE(metadata, '$.document_name') FROM documents")
        rows = cursor.fetchall()
        document_names = [r[0] for r in rows if r[0]]
        
        print(f"Total de documentos identificados no Oracle: {len(document_names)}")
        
        for idx, doc_name in enumerate(document_names, 1):
            print(f"\n[{idx}/{len(document_names)}] Analisando obra: {doc_name}")
            
            # Verificar se já tem metadados do Gemini em algum chunk para economizar chamadas
            cursor.execute(
                "SELECT id, metadata FROM documents WHERE JSON_VALUE(metadata, '$.document_name') = :doc_name",
                doc_name=doc_name
            )
            chunks = cursor.fetchall()
            if not chunks:
                print(f"  Nenhum bloco encontrado para o documento: {doc_name}")
                continue
                
            raw_meta_val = chunks[0][1]
            meta_str = raw_meta_val.read() if hasattr(raw_meta_val, "read") else raw_meta_val
            
            try:
                first_chunk_metadata = json.loads(meta_str) if meta_str else {}
            except Exception:
                first_chunk_metadata = {}
                
            if "extracted_entities" in first_chunk_metadata and "sentiment" in first_chunk_metadata:
                print(f"  [Ignorado] Documento já enriquecido com dados do Gemini.")
                continue
                
            # 2. Obter os primeiros blocos de texto (até 8000 caracteres) para analisar
            cursor.execute(
                "SELECT content FROM documents WHERE JSON_VALUE(metadata, '$.document_name') = :doc_name "
                "ORDER BY TO_NUMBER(JSON_VALUE(metadata, '$.chunk_index')) ASC",
                doc_name=doc_name
            )
            content_rows = cursor.fetchall()
            
            sample_text = ""
            for r in content_rows:
                if len(sample_text) < 8000:
                    raw_content = r[0]
                    content_str = raw_content.read() if hasattr(raw_content, "read") else raw_content
                    if content_str:
                        sample_text += " " + content_str
                else:
                    break
                    
            sample_text = sample_text.strip()
            if not sample_text:
                print("  [Aviso] Nenhum texto encontrado para análise.")
                continue
                
            # 3. Chamar a API do Gemini NLU (Gratuito)
            print(f"  Chamando Gemini Flash NLU para '{doc_name}' ({len(sample_text)} caracteres)...")
            try:
                nlu_res = analyze_text_entities_and_sentiment_gemini(sample_text)
                extracted_entities = [ent.get("name") for ent in nlu_res.get("entities", []) if ent.get("name")]
                sentiment_data = nlu_res.get("sentiment", {"score": 0.0, "label": "NEUTRAL"})
                
                print(f"  [Entidades extraídas]: {extracted_entities[:5]}")
                print(f"  [Sentimento]: {sentiment_data}")
            except Exception as gem_err:
                print(f"  [ERRO GEMINI] Falha ao analisar o documento: {gem_err}")
                continue
                
            # 4. Atualizar os metadados de todos os chunks deste documento no Oracle
            print(f"  Atualizando {len(chunks)} blocos no Oracle...")
            updated_count = 0
            for chunk_id, raw_meta_val in chunks:
                meta_str = raw_meta_val.read() if hasattr(raw_meta_val, "read") else raw_meta_val
                try:
                    meta = json.loads(meta_str) if meta_str else {}
                except Exception:
                    meta = {}
                meta["extracted_entities"] = extracted_entities
                meta["sentiment"] = sentiment_data
                
                cursor.execute(
                    "UPDATE documents SET metadata = :meta_json WHERE id = :chunk_id",
                    meta_json=json.dumps(meta),
                    chunk_id=chunk_id
                )
                updated_count += 1
                
            conn.commit()
            print(f"  [SUCESSO] {updated_count} blocos atualizados para '{doc_name}'")
            
            # Evitar estourar o rate limit de 15 RPM da API Key gratuita do Gemini
            print("  Aguardando 4 segundos antes do próximo documento...")
            time.sleep(4)
            
    except Exception as e:
        print(f"[ERRO GERAL] Falha na migração: {e}")
    finally:
        cursor.close()
        conn.close()
        print("\n--- PROCESSO DE ENRIQUECIMENTO FINALIZADO ---")

if __name__ == "__main__":
    enrich_database_metadata()
