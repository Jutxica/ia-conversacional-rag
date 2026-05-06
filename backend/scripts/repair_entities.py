import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CORPUS_DIR = os.getenv("CORPUS_DIR", "backend/data/dehon_corpus")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    logger.error("Credenciais Supabase ausentes!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_entities_from_json(data: Dict, start_par: int, end_par: int) -> Dict[str, List[str]]:
    """Extrai entidades corrigindo a busca em documentRef."""
    entities = {"people": [], "places": [], "concepts": []}
    
    # Busca maps no root ou no documentRef
    doc_ref = data.get('documentRef', {}) if isinstance(data.get('documentRef'), dict) else {}
    
    maps = {
        "people": data.get('peoplemap') or doc_ref.get('peoplemap') or {},
        "places": data.get('placesmap') or doc_ref.get('placesmap') or {},
        "concepts": data.get('conceptsmap') or doc_ref.get('conceptsmap') or {}
    }
    
    for key, val in maps.items():
        if isinstance(val, str):
            try:
                maps[key] = json.loads(val)
            except:
                maps[key] = {}

    for category, mapping in maps.items():
        if not isinstance(mapping, dict): continue
        for entity_name, mentions in mapping.items():
            if not isinstance(mentions, list): continue
            for mention in mentions:
                par_index = mention.get('par')
                if par_index is not None:
                    try:
                        p_idx = int(par_index)
                        if start_par <= p_idx <= end_par:
                            if entity_name not in entities[category]:
                                entities[category].append(entity_name)
                    except:
                        continue
    
    return entities

def repair_metadata():
    logger.info("Iniciando reparo de metadados com paginação...")
    
    page_size = 1000
    offset = 0
    updated_count = 0
    total_processed = 0
    
    while True:
        # Puxa documentos em lotes
        res = supabase.table("documents").select("id, metadata").range(offset, offset + page_size - 1).execute()
        docs = res.data or []
        
        if not docs:
            break
            
        logger.info(f"Processando lote: {offset} até {offset + len(docs)}")
        
        for doc in tqdm(docs):
            total_processed += 1
            doc_id = doc['id']
            metadata = doc['metadata']
            source_id = metadata.get('source_id')
            
            if not source_id: continue
            
            file_path = os.path.join(CORPUS_DIR, source_id)
            if not os.path.exists(file_path): continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                par_range = metadata.get('par_range', [0, 9999])
                start_par, end_par = par_range[0], par_range[1]
                
                # Recalcula entidades com a lógica corrigida
                new_entities = get_entities_from_json(data, start_par, end_par)
                
                # Extrai destinatários (receivers)
                ps = data.get('prosearch', {})
                if not ps and 'documentRef' in data:
                    ps = data['documentRef'].get('prosearch', {})
                
                receivers = ps.get('receivers', [])
                destinatario = ps.get('receiver') or ps.get('destinatario')
                
                # Verifica se houve mudança real
                needs_update = False
                if new_entities != metadata.get('entities'):
                    metadata['entities'] = new_entities
                    needs_update = True
                
                if receivers and receivers != metadata.get('receivers'):
                    metadata['receivers'] = receivers
                    needs_update = True
                    
                if destinatario and destinatario != metadata.get('destinatario'):
                    metadata['destinatario'] = destinatario
                    needs_update = True
                
                if needs_update:
                    supabase.table("documents").update({"metadata": metadata}).eq("id", doc_id).execute()
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar {source_id}: {e}")
        
        offset += page_size

    logger.info(f"Reparo concluído. {total_processed} analisados, {updated_count} documentos atualizados.")

if __name__ == "__main__":
    repair_metadata()
