import os
import tempfile
from typing import Union
from pypdf import PdfReader

# Procura pelas credenciais do Google Cloud
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us")
GOOGLE_PROCESSOR_ID = os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID")

def is_document_ai_configured() -> bool:
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    processor_id = os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID")
    has_creds = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64"))
    return bool(project_id and processor_id and has_creds)

def setup_google_credentials():
    """Se a credencial estiver no formato Base64 no env, escreve em um arquivo temporário."""
    creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")
    if creds_b64 and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        import base64
        try:
            decoded = base64.b64decode(creds_b64)
            temp_creds = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            temp_creds.write(decoded)
            temp_creds.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds.name
            print(f"[Google Cloud] Credenciais de conta de serviço configuradas via b64 em: {temp_creds.name}")
        except Exception as e:
            print(f"[Google Cloud] Falha ao decodificar GOOGLE_CREDENTIALS_JSON_BASE64: {e}")

# Executa setup de credenciais b64 se existirem no ambiente
setup_google_credentials()

def extract_text_using_document_ai(file_content: bytes) -> str:
    """Extrai texto de um PDF usando a API do Google Document AI OCR de alta precisão."""
    from google.cloud import documentai
    
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    location = os.getenv("GOOGLE_LOCATION", "us")
    processor_id = os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID")
    
    if not project_id or not processor_id:
        raise ValueError("Google Project ID e Processor ID são obrigatórios para Document AI.")
        
    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(project_id, location, processor_id)
    raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")
    
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    
    return result.document.text

def extract_text_using_pypdf(file_content: bytes) -> str:
    """Fallback local usando PyPDF para extrair texto básico se as credenciais do Google estiverem ausentes."""
    import io
    try:
        reader = PdfReader(io.BytesIO(file_content))
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n\n"
        return full_text
    except Exception as e:
        print(f"[PyPDF Fallback] Erro ao extrair texto com PyPDF: {e}")
        return ""

def extract_text_from_pdf(pdf_source: Union[str, bytes]) -> str:
    """Função unificada de extração. Usa Document AI se configurado, ou cai no fallback do PyPDF."""
    file_content: bytes = b""
    
    if isinstance(pdf_source, str):
        if not os.path.exists(pdf_source):
            raise FileNotFoundError(f"Arquivo PDF não encontrado no caminho: {pdf_source}")
        with open(pdf_source, "rb") as f:
            file_content = f.read()
    elif isinstance(pdf_source, bytes):
        file_content = pdf_source
    else:
        raise TypeError("A fonte do PDF deve ser um caminho de arquivo (str) ou bytes.")
        
    if is_document_ai_configured():
        try:
            print("[Google OCR] Enviando PDF para o Google Document AI...")
            text = extract_text_using_document_ai(file_content)
            if text and len(text.strip()) > 50:
                print(f"[Google OCR] Sucesso: {len(text)} caracteres extraídos.")
                return text
            print("[Google OCR] Aviso: Document AI retornou texto vazio ou muito curto. Usando fallback.")
        except Exception as e:
            print(f"[Google OCR] Falha ao processar com Document AI: {e}. Usando fallback do PyPDF.")
            
    # Fallback
    print("[Google OCR] Usando extração local via PyPDF.")
    return extract_text_using_pypdf(file_content)
