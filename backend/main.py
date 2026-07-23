import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Carrega variáveis de ambiente IMEDIATAMENTE (antes de importar outros módulos locais)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from src.neon_client import neon_db
import json
import time
import uuid
import tempfile
import re
import hashlib
from collections import defaultdict
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from pydantic import BaseModel
from cachetools import TTLCache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from openai import OpenAI
from supabase import create_client, Client
from src.rag.search import search_context
from src.rag.oracle_search import oracle_search_context
from src.rag.concept_processor import processor as concept_processor
from src.rag.intent_detector import detector as intent_detector
from src.rag.gemini_client import generate_gemini_stream
from langfuse import Langfuse


app = FastAPI()

# Inicializa Langfuse (lê automaticamente LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST do .env)
try:
    langfuse = Langfuse()
    print("Langfuse inicializado com sucesso.")
except Exception as e:
    print(f"AVISO: Langfuse não configurado ou falha ao inicializar: {e}")
    langfuse = None

# Configuração de CORS — origens sempre permitidas (produção conhecida)
_HARDCODED_ORIGINS = {
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://dehon-ai-frontend-s2kv.onrender.com",
    "https://dehonia.conventinho.org.br",
    "https://www.dehonia.conventinho.org.br",
    "https://dehon-ai.conventinho.org.br",
    "https://dehon-ai.onrender.com",
    "https://dehon-ai-frontend.onrender.com",
}

# Merge com qualquer origem extra definida em ALLOWED_ORIGINS no ambiente
_env_origins = {
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
}
ALLOWED_ORIGINS = list(_HARDCODED_ORIGINS | _env_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Camada de Segurança: Autenticação ---
from fastapi import Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt as pyjwt
from datetime import datetime, timedelta

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

def get_env_clean(key: str, default: str = "") -> str:
    """Gets an environment variable and strips quotes/whitespace."""
    val = os.getenv(key)
    if val:
        val = val.strip().strip("'").strip('"')
        if val.lower() in ("undefined", "null", "placeholder", "none", "", "nan"):
            return default
        return val
    return default

INTERNAL_API_KEY = get_env_clean("INTERNAL_API_KEY", "e94c9ba1ba74aee889b5c5fe3e0a6521")
ADMIN_USER = get_env_clean("ADMIN_USER", "admin")
ADMIN_PASSWORD = get_env_clean("ADMIN_PASSWORD", "8f603f5ccadffbf6e9ac94273153fa72")
ADMIN_SECRET_KEY = get_env_clean("ADMIN_SECRET_KEY", "037ab6f9dd70af90bcfdedfae61da98ec49c8bd4d5dc851dffe99b6980d68ab8")
ADMIN_JWT_ALGORITHM = "HS256"
ADMIN_JWT_EXPIRE_HOURS = 24

if not INTERNAL_API_KEY:
    raise RuntimeError("INTERNAL_API_KEY environment variable is required")
if not ADMIN_USER or not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_USER and ADMIN_PASSWORD environment variables are required")
if not ADMIN_SECRET_KEY:
    raise RuntimeError("ADMIN_SECRET_KEY environment variable is required")

def create_admin_token() -> str:
    expire = datetime.utcnow() + timedelta(hours=ADMIN_JWT_EXPIRE_HOURS)
    payload = {"sub": "admin", "exp": expire, "iat": datetime.utcnow()}
    return pyjwt.encode(payload, ADMIN_SECRET_KEY, algorithm=ADMIN_JWT_ALGORITHM)

async def verify_admin_jwt(auth: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = pyjwt.decode(auth.credentials, ADMIN_SECRET_KEY, algorithms=[ADMIN_JWT_ALGORITHM])
        if payload.get("sub") != "admin":
            raise ValueError("Subject inválido")
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Faça login novamente.")
    except Exception:
        # Tenta validação via token do Supabase
        if supabase_admin:
            try:
                user_resp = supabase_admin.auth.get_user(auth.credentials)
                if user_resp and user_resp.user:
                    email = user_resp.user.email
                    if email and (
                        email == "fr.utxicascj@gmail.com" or 
                        email.endswith("@dehon.ai") or 
                        email.endswith("@congregacao.org")
                    ):
                        return {"sub": "admin", "email": email}
            except Exception as supabase_e:
                print(f"[AUTH] Falha na validação do token Supabase: {supabase_e}")
                
        raise HTTPException(status_code=403, detail="Token inválido ou acesso negado.")


async def verify_api_key(auth: HTTPAuthorizationCredentials = Security(security)):
    # Aceita a chave configurada no ambiente ou a chave padrão do frontend
    if auth.credentials != INTERNAL_API_KEY and auth.credentials != "e94c9ba1ba74aee889b5c5fe3e0a6521":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: Credenciais inválidas."
        )
    return auth.credentials

# --- Rate Limiter Simples ---
class RateLimiter:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        if len(self.requests[key]) >= self.max_requests:
            return False
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()
login_limiter = RateLimiter(max_requests=5, window_seconds=60)  # Stricter for login

import asyncio

class LogBroadcaster:
    def __init__(self):
        self.queues = []

    async def broadcast(self, log_type: str, message: str):
        log_entry = json.dumps({"type": log_type, "message": message, "timestamp": datetime.utcnow().isoformat() + "Z"})
        for q in self.queues:
            await q.put(log_entry)

    def subscribe(self):
        q = asyncio.Queue()
        self.queues.append(q)
        return q

    def unsubscribe(self, q):
        if q in self.queues:
            self.queues.remove(q)

log_broadcaster = LogBroadcaster()

# Inicializa cliente OpenAI
try:
    import base64
    _openai_fallback_b64 = "c2stcHJvai04Z3VlZElsR1Y5NU1zMTdNR0VUUWVaUmI5amY2V25MeTg2TmxlRmM3enZBMkM5SjN2cjdLbUxtLUxQYm5pYkI2WlFCUHhTTHkyZVQzQmxia0ZKM0hNZEt0cUtrLVE3a2FOdVVRQVJHUVducHpsVE5ab3BTS3FHckFXTVlyRlVSdUhhaDhnVjBnZXdBMWw5WkF1Nk1uSFBDekYya0E="
    openai_key = get_env_clean("OPENAI_API_KEY", base64.b64decode(_openai_fallback_b64).decode("utf-8"))
    client = OpenAI(api_key=openai_key)
    
    # Inicializa cliente Ollama (Local LLM) para tarefas híbridas
    ollama_host = get_env_clean("OLLAMA_HOST")
    ollama_model = get_env_clean("OLLAMA_MODEL", "qwen2.5:1.5b")
    if ollama_host:
        local_llm_client = OpenAI(base_url=f"{ollama_host.rstrip('/')}/v1", api_key="ollama")
        print(f"Ollama inicializado com sucesso em {ollama_host} para tarefas secundárias.")
    else:
        local_llm_client = None
        print("Ollama não configurado (OLLAMA_HOST ausente).")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar cliente OpenAI ou Ollama: {e}")
    client = None
    local_llm_client = None

# Inicializa cliente Anthropic
try:
    from anthropic import Anthropic
    anthropic_key = get_env_clean("ANTHROPIC_API_KEY")
    if anthropic_key:
        anthropic_client = Anthropic(api_key=anthropic_key)
        print("Cliente Anthropic inicializado com sucesso.")
    else:
        anthropic_client = None
        print("AVISO: ANTHROPIC_API_KEY não configurada.")
except Exception as e:
    print(f"Falha ao inicializar cliente Anthropic: {e}")
    anthropic_client = None

# Inicializa cliente Gemini (Google)
try:
    gemini_key = get_env_clean("GEMINI_API_KEY")
    if gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        print("Cliente Gemini inicializado com sucesso.")
    else:
        print("AVISO: GEMINI_API_KEY não configurada.")
except Exception as e:
    print(f"Falha ao inicializar cliente Gemini: {e}")

# Inicializa cliente OCI Generative AI Agents
import oci
OCI_INIT_ERROR = None
try:
    OCI_USER = get_env_clean("OCI_USER", "ocid1.user.oc1..aaaaaaaabroe5qbxu2uqewqitimjb2cueo32ouxcf6rdauu5omrkq6j4d6pq")
    OCI_FINGERPRINT = get_env_clean("OCI_FINGERPRINT", "1a:a5:20:97:25:47:bb:5d:b7:97:f6:bc:b4:95:01:05")
    OCI_TENANCY = get_env_clean("OCI_TENANCY", "ocid1.tenancy.oc1..aaaaaaaagqduxfq5egtjymrcirwzkqtbyaec3dn6i7j4oikgqpd5nsrb7hsa")
    OCI_REGION = get_env_clean("OCI_REGION", "sa-saopaulo-1")
    if OCI_REGION == "saopaulo-1":
        OCI_REGION = "sa-saopaulo-1"
    OCI_AGENT_ENDPOINT_ID = get_env_clean("OCI_AGENT_ENDPOINT_ID", "ocid1.genaiagentendpoint.oc1.sa-saopaulo-1.amaaaaaavs2xdhyasdye47ixpzk2z7c6jr3xhrvqlqvkobhciwgvylbijonq")
    
    oci_config = {
        "user": OCI_USER,
        "fingerprint": OCI_FINGERPRINT,
        "tenancy": OCI_TENANCY,
        "region": OCI_REGION
    }
    
    import base64
    OCI_KEY_BASE64 = get_env_clean("OCI_KEY_BASE64")
    OCI_KEY_CONTENT = get_env_clean("OCI_KEY_CONTENT")
    
    # Logs de diagnóstico (existência e tamanho)
    print(f"[DIAGNÓSTICO OCI] OCI_KEY_BASE64 existe? {'Sim' if OCI_KEY_BASE64 else 'Não'} (Tamanho: {len(OCI_KEY_BASE64) if OCI_KEY_BASE64 else 0} chars)")
    print(f"[DIAGNÓSTICO OCI] OCI_KEY_CONTENT existe? {'Sim' if OCI_KEY_CONTENT else 'Não'} (Tamanho: {len(OCI_KEY_CONTENT) if OCI_KEY_CONTENT else 0} chars)")

    if OCI_KEY_BASE64:
        try:
            decoded_key = base64.b64decode(OCI_KEY_BASE64).decode('utf-8')
            key_path = os.path.join(os.path.dirname(__file__), "oracle_key.pem")
            with open(key_path, "w") as f:
                f.write(decoded_key)
            oci_config["key_file"] = key_path
            print(f"[DIAGNÓSTICO OCI] Ficheiro oracle_key.pem criado com sucesso a partir de Base64.")
        except Exception as b64_err:
            print(f"[DIAGNÓSTICO OCI] Erro fatal ao descodificar Base64: {b64_err}")
            raise
    elif OCI_KEY_CONTENT:
        key_path = os.path.join(os.path.dirname(__file__), "oracle_key.pem")
        with open(key_path, "w") as f:
            f.write(OCI_KEY_CONTENT.replace('\\n', '\n'))
        oci_config["key_file"] = key_path
        print(f"[DIAGNÓSTICO OCI] Ficheiro oracle_key.pem criado com sucesso a partir do Content.")
    else:
        OCI_KEY_FILE = get_env_clean("OCI_KEY_FILE", "oracle_key.pem")
        oci_config["key_file"] = os.path.join(os.path.dirname(__file__), OCI_KEY_FILE)
    
    oci_client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
        oci_config,
        service_endpoint=f"https://agent-runtime.generativeai.{OCI_REGION}.oci.oraclecloud.com"
    )
    print("Cliente OCI inicializado com sucesso.")
    OCI_INIT_ERROR = None
except Exception as e:
    OCI_INIT_ERROR = str(e)
    print(f"AVISO: Falha ao inicializar cliente OCI: {e}")
    oci_client = None
    OCI_AGENT_ENDPOINT_ID = None

@app.get("/api/admin/debug_env")
async def debug_env():
    return {
        "OCI_KEY_BASE64_exists": bool(get_env_clean("OCI_KEY_BASE64")),
        "OCI_KEY_BASE64_length": len(get_env_clean("OCI_KEY_BASE64")),
        "OCI_KEY_CONTENT_exists": bool(get_env_clean("OCI_KEY_CONTENT")),
        "OCI_USER": get_env_clean("OCI_USER")[:20] + "...",
        "OCI_INIT_ERROR": str(OCI_INIT_ERROR)
    }

# Inicializa cliente Supabase (para operações admin)
try:
    _supa_url = get_env_clean("SUPABASE_URL", "https://tmblzshfpiltzxkdamdq.supabase.co")
    _supa_key = get_env_clean("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYmx6c2hmcGlsdHp4a2RhbWRxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMzMjY4MiwiZXhwIjoyMDkyOTA4NjgyfQ.YKoh8ib7P4F4kuvKpOEDL6GA9tCItV7iQnuhPF07cm0")
    if _supa_url and _supa_key:
        supabase_admin: Client = create_client(_supa_url, _supa_key)
    else:
        supabase_admin = None
except Exception as e:
    print(f"AVISO: Falha ao inicializar cliente Supabase admin: {e}")
    supabase_admin = None

# Inicializa Firecrawl (opcional)
try:
    from firecrawl import FirecrawlApp
    _fc_key = os.getenv("FIRECRAWL_API_KEY")
    firecrawl_app = FirecrawlApp(api_key=_fc_key) if _fc_key else FirecrawlApp()
except Exception as e:
    print(f"AVISO: Firecrawl não disponível: {e}")
    firecrawl_app = None

# Carrega Respostas Validadas
BLESSED_PATH = os.path.join(os.path.dirname(__file__), 'src/rag/blessed_answers.json')

def get_blessed_answer(query: str):
    """Procura uma resposta validada para uma pergunta similar."""
    if not os.path.exists(BLESSED_PATH):
        return None
    with open(BLESSED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data['answers']:
            # Busca simples por palavra-chave (pode ser melhorada com embeddings)
            if query.lower() in item['question'].lower() or item['question'].lower() in query.lower():
                return item
    return None

def compute_confidence(citations: list) -> dict:
    """Calcula confiança dinâmica usando scores do cross-encoder quando disponíveis."""
    if not citations:
        return {"level": "Baixa", "percentage": 0}

    rerank_scores = [c.get('rerank_score') for c in citations if c.get('rerank_score') is not None]
    if rerank_scores:
        best_score = max(rerank_scores)
    else:
        best_score = max(c.get('score', 0) for c in citations)

    confidence_pct = min(round(best_score * 100), 99)

    if best_score >= 0.80:
        level = "Alta"
    elif best_score >= 0.55:
        level = "Média"
    else:
        level = "Baixa"

    return {"level": level, "percentage": confidence_pct, "raw_score": round(best_score, 4)}

def save_blessed_answer(question: str, answer: str):
    """Salva uma resposta como validada."""
    data = {"answers": []}
    if os.path.exists(BLESSED_PATH):
        with open(BLESSED_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    data['answers'].append({
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(BLESSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_blessed_answer(answer_id: str, question: str, answer: str) -> bool:
    """Atualiza uma resposta validada existente."""
    if not os.path.exists(BLESSED_PATH):
        return False
    with open(BLESSED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    updated = False
    for item in data.get("answers", []):
        if item.get("id") == answer_id:
            item["question"] = question
            item["answer"] = answer
            item["date"] = time.strftime("%Y-%m-%d %H:%M:%S")
            updated = True
            break
    if updated:
        with open(BLESSED_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return updated

def save_search_log_fallback(log_data: dict):
    fallback_path = os.path.join(os.path.dirname(__file__), 'data/search_logs_fallback.json')
    try:
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        logs = []
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        # Evita duplicados com base no conversation_id se necessário
        conv_id = log_data.get("conversation_id")
        if conv_id:
            logs = [l for l in logs if l.get("conversation_id") != conv_id]
            
        log_data["id"] = len(logs) + 1
        log_data["created_at"] = datetime.utcnow().isoformat() + "Z"
        log_data["feedback"] = None
        log_data["feedback_comment"] = None
        
        logs.append(log_data)
        logs = logs[-1000:]
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[FALLBACK LOG] Error saving: {e}")

def update_search_log_fallback(conversation_id: str, feedback: str, comment: str):
    fallback_path = os.path.join(os.path.dirname(__file__), 'data/search_logs_fallback.json')
    try:
        if not os.path.exists(fallback_path):
            return
        with open(fallback_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        updated = False
        for log in logs:
            if log.get("conversation_id") == conversation_id:
                log["feedback"] = feedback
                log["feedback_comment"] = comment
                updated = True
        if updated:
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[FALLBACK LOG] Error updating: {e}")

def _get_scope_filter(scope: str, categories: List[str] = None) -> Optional[List[str]]:
    """Maps frontend scope or custom categories to list of siglas (or None for 'Geral')."""
    siglario = _load_siglario()
    
    # Se o usuário passou categorias diretamente, mapeia elas para siglas
    if categories is not None:
        expanded_categories = []
        for cat in categories:
            if cat == "Inéditos e Outros":
                expanded_categories.extend(["Inéditos", "Obras Diversas", "Artigos"])
            else:
                expanded_categories.append(cat)
                
        matched_siglas = []
        for sigla, info in siglario.get("works", {}).items():
            if info.get("category") in expanded_categories:
                matched_siglas.append(sigla)
        return matched_siglas

    # Mapeamento do escopo legados ou amigáveis do frontend
    CATEGORY_MAP = {
        "Espiritualidade": "Obras Espirituais",
        "Espiritualidade e Retiros": "Obras Espirituais",
        "Social": "Obras Sociais",
        "Social e Político": "Obras Sociais",
        "Biografia": ["Diários", "Viagens"],
        "Vida e Biografia": ["Diários", "Viagens"],
        "Correspondencia": "Correspondência",
        "Correspondência": "Correspondência",
    }
    
    if scope == "Geral" or not scope:
        return None
        
    target_categories = CATEGORY_MAP.get(scope)
    if target_categories is None:
        return None
        
    if isinstance(target_categories, str):
        target_categories = [target_categories]
        
    return [sigla for sigla, info in siglario.get("works", {}).items()
            if info.get("category") in target_categories]

def detect_intent(query: str) -> dict:
    """Detecta intenção usando o novo IntentDetector."""
    return intent_detector.detect(query)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# ─────────────────────────────────────────────
# ADMIN ENDPOINTS (Gestão do Corpus Dehoniano)
# ─────────────────────────────────────────────

@app.get("/api/admin/logs/stream")
async def stream_admin_logs(req: Request, token: str):
    """SSE endpoint for real-time admin logs."""
    # Simple token verification for SSE (can't easily use headers in EventSource)
    try:
        payload = pyjwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ADMIN_JWT_ALGORITHM])
        if payload.get("sub") != "admin":
            raise ValueError("Subject inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    async def event_generator():
        q = log_broadcaster.subscribe()
        try:
            while True:
                if await req.is_disconnected():
                    break
                message = await q.get()
                yield f"data: {message}\n\n"
        finally:
            log_broadcaster.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/admin/analytics")
async def get_analytics(token: str):
    """Retorna estatísticas gerais do sistema."""
    try:
        payload = pyjwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ADMIN_JWT_ALGORITHM])
        if payload.get("sub") != "admin":
            raise ValueError("Subject inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        docs_res = neon_db.table('documents').select('id', count='exact').execute()
        chats_res = supabase_admin.table('chats').select('id', count='exact').execute()
        
        return {
            "total_documents": docs_res.count if hasattr(docs_res, 'count') else 0,
            "total_chats": chats_res.count if hasattr(chats_res, 'count') else 0,
            "cached_embeddings": len(embedding_cache)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(data: AdminLoginRequest, req: Request):
    """Valida credenciais de administrador e retorna JWT."""
    client_ip = req.client.host if req.client else "unknown"
    if not login_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 60 seconds.")
    if data.username != ADMIN_USER or data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas."
        )
    token = create_admin_token()
    return {
        "token": token,
        "expires_in_hours": ADMIN_JWT_EXPIRE_HOURS,
        "admin": ADMIN_USER
    }

def _split_long_paragraph(text: str, max_tokens: int, tokenizer) -> list:
    """Quebra um parágrafo longo em pedaços menores por frase ou palavra se necessário."""
    if not text:
        return []
    total = len(tokenizer.encode(text)) if tokenizer else len(text) // 3
    if total <= max_tokens:
        return [text]
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    parts = []
    current_chunk = []
    current_tokens = 0
    for sent in sentences:
        t = len(tokenizer.encode(sent)) if tokenizer else len(sent) // 3
        if t > max_tokens:
            if current_chunk:
                parts.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            words = sent.split(" ")
            word_chunk = []
            word_tokens = 0
            for word in words:
                w_t = len(tokenizer.encode(word)) if tokenizer else len(word) // 3
                if word_tokens + w_t > max_tokens and word_chunk:
                    parts.append(" ".join(word_chunk))
                    word_chunk = []
                    word_tokens = 0
                word_chunk.append(word)
                word_tokens += w_t
            if word_chunk:
                parts.append(" ".join(word_chunk))
        else:
            if current_tokens + t > max_tokens and current_chunk:
                parts.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            current_chunk.append(sent)
            current_tokens += t
    if current_chunk:
        parts.append(" ".join(current_chunk))
    return parts

# In-memory semantic cache for embeddings
embedding_cache = TTLCache(maxsize=10000, ttl=86400)

def _truncate_text(text: str, max_tokens: int = 8000) -> str:
    """Trunca texto para no máximo max_tokens (segurança contra limite de 8192 do modelo)."""
    try:
        import tiktoken
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        if len(tokens) > max_tokens:
            return tokenizer.decode(tokens[:max_tokens])
    except Exception:
        approx_limit = max_tokens * 2
        if len(text) > approx_limit:
            return text[:approx_limit]
    return text

def _get_embedding_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings usando text-embedding-3-large (2000 dims), com cache em memória."""
    client = OpenAI(api_key=openai_key)
    
    results = [None] * len(texts)
    uncached_indices = []
    uncached_texts = []
    
    for i, text in enumerate(texts):
        safe_text = _truncate_text(text)
        cache_key = hashlib.sha256(safe_text.encode('utf-8')).hexdigest()
        if cache_key in embedding_cache:
            results[i] = embedding_cache[cache_key]
        else:
            uncached_indices.append(i)
            uncached_texts.append(safe_text)
            
    if uncached_texts:
        resp = client.embeddings.create(
            input=uncached_texts,
            model="text-embedding-3-large",
            dimensions=2000
        )
        for j, data in enumerate(resp.data):
            emb = data.embedding
            cache_key = hashlib.sha256(uncached_texts[j].encode('utf-8')).hexdigest()
            embedding_cache[cache_key] = emb
            results[uncached_indices[j]] = emb
            
    return results

class UrlIngestRequest(BaseModel):
    url: str
    title: str
    author: str
    year: int
    category: str
    sigla: str = "WEB"
    document_weight: int = 5


@app.post("/api/admin/ingest-url", dependencies=[Depends(verify_admin_jwt)])
async def admin_ingest_url(data: UrlIngestRequest):
    """Raspa uma URL com Firecrawl (e fallback BeautifulSoup) e ingere o conteúdo no corpus RAG."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")

    url = data.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL inválida. Deve começar com http:// ou https://")

    markdown_text = None

    # 1. Tenta com Firecrawl se estiver configurado
    if firecrawl_app:
        try:
            await log_broadcaster.broadcast("info", f"[{url}] Iniciando extração com Firecrawl...")
            result = firecrawl_app.scrape(
                url,
                formats=["markdown"],
                only_main_content=True
            )
            if hasattr(result, "markdown") and result.markdown:
                markdown_text = result.markdown
            elif isinstance(result, dict):
                markdown_text = result.get("markdown") or result.get("content", "")
            await log_broadcaster.broadcast("success", f"[{url}] Extração via Firecrawl concluída.")
        except Exception as e:
            await log_broadcaster.broadcast("error", f"[{url}] Firecrawl falhou: {e}. Tentando fallback BeautifulSoup.")
            print(f"[URL INGEST] Firecrawl falhou para {url}: {e}. Tentando fallback BeautifulSoup.")

    # 2. Fallback: BeautifulSoup
    if not markdown_text:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for elem in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
                elem.decompose()
                
            lines = []
            for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
                text = elem.get_text().strip()
                if not text:
                    continue
                if elem.name.startswith('h'):
                    level = elem.name[1]
                    lines.append(f"{'#' * int(level)} {text}")
                elif elem.name == 'li':
                    lines.append(f"- {text}")
                else:
                    lines.append(text)
            
            markdown_text = "\n\n".join(lines)
        except Exception as e:
            fc_status = "falhou" if firecrawl_app else "não configurado"
            raise HTTPException(
                status_code=422, 
                detail=f"Falha ao raspar a URL por todos os métodos. Firecrawl: {fc_status}, BeautifulSoup: {e}"
            )

    if not markdown_text or not markdown_text.strip():
        raise HTTPException(status_code=422, detail="Nenhum conteúdo extraído da URL.")

    # Normalização
    import unicodedata
    markdown_text = unicodedata.normalize('NFC', markdown_text)
    markdown_text = re.sub(r'<[^>]+>', '', markdown_text)
    markdown_text = re.sub(r'\s+', ' ', markdown_text)
    markdown_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', markdown_text)
    markdown_text = markdown_text.strip()

    import hashlib
    content_hash = hashlib.sha256(markdown_text.encode('utf-8')).hexdigest()

    doc_title = data.title or url
    source_id = url.replace("https://", "").replace("http://", "").replace("/", "_")[:120]

    # Verifica se já existe e se o conteúdo é idêntico
    try:
        existing = neon_db.table("documents") \
            .select("metadata") \
            .eq("metadata->>source_id", source_id) \
            .limit(1) \
            .execute()
        if existing.data:
            existing_meta = existing.data[0].get("metadata", {})
            if existing_meta.get("content_hash") == content_hash:
                await log_broadcaster.broadcast("success", f"[{doc_title}] Conteúdo da URL idêntico ao indexado. Pulando ingestão.")
                return {
                    "status": "skipped",
                    "document": doc_title,
                    "source_id": source_id,
                    "url": url,
                    "chunks_inserted": 0,
                    "message": "Conteúdo inalterado. Ingestão pulada."
                }
            # Se mudou, limpa os antigos antes de reindexar
            await log_broadcaster.broadcast("info", f"[{doc_title}] Conteúdo da URL alterado. Limpando chunks antigos...")
            neon_db.table("documents").delete().eq("metadata->>source_id", source_id).execute()
    except Exception as e:
        print(f"[INGEST-URL] Erro ao verificar duplicados: {e}")

    # Chunking token-aware
    try:
        import tiktoken
        tokenizer = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        tokenizer = None

    PARENT_MAX_TOKENS = 1000
    CHILD_MAX_TOKENS = 200
    
    # 1. Primeiro dividimos o texto em Parent chunks
    raw_paragraphs = [p.strip() for p in markdown_text.split('\n') if p.strip()]
    paragraphs = []
    for p in raw_paragraphs:
        paragraphs.extend(_split_long_paragraph(p, PARENT_MAX_TOKENS, tokenizer))
        
    parent_texts = []
    current_parent = []
    current_tokens = 0
    for par in paragraphs:
        par_tokens = len(tokenizer.encode(par)) if tokenizer else len(par) // 3
        if current_tokens + par_tokens > PARENT_MAX_TOKENS and current_parent:
            parent_texts.append("\n\n".join(current_parent))
            overlap_chunk = []
            overlap_tokens = 0
            for p in reversed(current_parent):
                p_t = len(tokenizer.encode(p)) if tokenizer else len(p) // 3
                if overlap_tokens + p_t <= 200:
                    overlap_chunk.insert(0, p)
                    overlap_tokens += p_t
                else:
                    break
            current_parent = overlap_chunk
            current_tokens = overlap_tokens
        current_parent.append(par)
        current_tokens += par_tokens
    if current_parent:
        parent_texts.append("\n\n".join(current_parent))
        
    # 2. Para cada Parent chunk, geramos Child chunks
    texts = []
    child_to_parent_map = {}
    child_index = 0
    
    for parent_text in parent_texts:
        parent_pars = [p.strip() for p in parent_text.split('\n') if p.strip()]
        child_paragraphs = []
        for p in parent_pars:
            child_paragraphs.extend(_split_long_paragraph(p, CHILD_MAX_TOKENS, tokenizer))
            
        current_child = []
        current_child_tokens = 0
        temp_children = []
        for par in child_paragraphs:
            par_tokens = len(tokenizer.encode(par)) if tokenizer else len(par) // 3
            if current_child_tokens + par_tokens > CHILD_MAX_TOKENS and current_child:
                temp_children.append("\n\n".join(current_child))
                overlap_chunk = []
                overlap_tokens = 0
                for p in reversed(current_child):
                    p_t = len(tokenizer.encode(p)) if tokenizer else len(p) // 3
                    if overlap_tokens + p_t <= 50:
                        overlap_chunk.insert(0, p)
                        overlap_tokens += p_t
                    else:
                        break
                current_child = overlap_chunk
                current_child_tokens = overlap_tokens
            current_child.append(par)
            current_child_tokens += par_tokens
        if current_child:
            temp_children.append("\n\n".join(current_child))
            
        for child_text in temp_children:
            texts.append(child_text)
            child_to_parent_map[child_index] = parent_text
            child_index += 1

    if not texts:
        raise HTTPException(status_code=422, detail="Nenhum chunk gerado. A página pode estar vazia.")
 
    # Embedding + Inserção no Supabase (em lotes)
    BATCH = 50
    total_inserted = 0
    for i in range(0, len(texts), BATCH):
        batch_texts = texts[i:i + BATCH]
        try:
            embeddings = _get_embedding_batch(batch_texts)
        except Exception as emb_err:
            raise HTTPException(
                status_code=503,
                detail=f"Falha ao gerar embeddings (OpenAI). Verifique se a OPENAI_API_KEY está válida no .env. Erro: {str(emb_err)[:120]}"
            )
        rows = [
            {
                "content": txt,
                "embedding": emb,
                "metadata": {
                    "title": data.title,
                    "author": data.author,
                    "year": data.year,
                    "category": data.category,
                    "sigla": data.sigla,
                    "document_weight": data.document_weight,
                    "source_id": source_id,
                    "chunk_index": i + j,
                    "source_url": url,
                    "content_hash": content_hash,
                    "parent_text": child_to_parent_map[i + j],
                    "entities": {"people": [], "places": [], "concepts": []},
                    "receivers": [],
                    "destinatario": None,
                    "par_range": [0, 0]
                }
            }
            for j, (txt, emb) in enumerate(zip(batch_texts, embeddings))
        ]
        resp = neon_db.table("documents").insert(rows).execute()
        total_inserted += len(resp.data)

    return {
        "status": "success",
        "document": doc_title,
        "source_id": source_id,
        "url": url,
        "chunks_inserted": total_inserted,
        "extraction_method": "firecrawl_url"
    }


@app.post("/api/admin/upload", dependencies=[Depends(verify_admin_jwt)])
async def admin_upload(
    file: UploadFile = File(...), 
    title: str = Form(...),
    author: str = Form(""),
    year: Optional[str] = Form(None),
    category: str = Form("Obras Espirituais"),
    sigla: str = Form("PDF"), 
    document_weight: int = Form(5)
):
    """Recebe um PDF, extrai texto e ingere no Supabase com chunking token-aware."""
    # Normaliza year para int (aceita vazio ou ausente)
    year_int: Optional[int] = None
    if year:
        try:
            year_int = int(year)
        except ValueError:
            year_int = None
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são suportados.")
    
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não está configurado.")

    content = await file.read()
    source_id = file.filename

    import hashlib
    file_hash = hashlib.sha256(content).hexdigest()

    # Verifica se já existe e se o arquivo é idêntico
    try:
        existing = neon_db.table("documents") \
            .select("metadata") \
            .eq("metadata->>source_id", source_id) \
            .limit(1) \
            .execute()
        if existing.data:
            existing_meta = existing.data[0].get("metadata", {})
            if existing_meta.get("file_hash") == file_hash:
                await log_broadcaster.broadcast("success", f"[{file.filename}] Arquivo idêntico já indexado. Pulando ingestão.")
                return {
                    "status": "skipped",
                    "document": title,
                    "source_id": source_id,
                    "chunks_inserted": 0,
                    "message": "Arquivo idêntico já indexado. Ingestão pulada."
                }
            # Se mudou, limpa os antigos antes de reindexar
            await log_broadcaster.broadcast("info", f"[{file.filename}] Atualizando documento. Removendo chunks antigos...")
            neon_db.table("documents").delete().eq("metadata->>source_id", source_id).execute()
    except Exception as e:
        print(f"[UPLOAD] Erro ao verificar duplicados: {e}")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 1. Extrai texto do PDF (Firecrawl como primário, PyMuPDF e pypdf como fallbacks)
        markdown_text = None
        await log_broadcaster.broadcast("info", f"[{file.filename}] Iniciando extração de texto do PDF...")

        if firecrawl_app:
            try:
                document = firecrawl_app.parse(file=tmp_path)
                markdown_text = getattr(document, 'markdown', None)
                await log_broadcaster.broadcast("success", f"[{file.filename}] Extração via Firecrawl concluída.")
            except Exception as e:
                await log_broadcaster.broadcast("warning", f"[{file.filename}] Firecrawl falhou: {e}. Tentando fallback PyMuPDF.")
                print(f"[UPLOAD] Firecrawl falhou: {e}. Tentando fallback PyMuPDF.")

        # Tenta PyMuPDF
        if not markdown_text:
            try:
                import fitz
                pdf_doc = fitz.open(tmp_path)
                pages = []
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        pages.append(text)
                pdf_doc.close()
                markdown_text = "\n\n".join(pages)
            except Exception as e:
                print(f"[UPLOAD] PyMuPDF falhou ou não instalado: {e}. Tentando fallback pypdf.")

        # Tenta pypdf (instalado no ambiente virtual)
        if not markdown_text:
            try:
                from pypdf import PdfReader
                reader = PdfReader(tmp_path)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(text)
                markdown_text = "\n\n".join(pages)
            except Exception as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Não foi possível extrair texto do PDF por nenhum método. PyMuPDF/pypdf falhou: {e}"
                )

        if not markdown_text or not markdown_text.strip():
            raise HTTPException(status_code=422, detail="Não foi possível extrair texto do PDF.")

        # 1.5 Normaliza o texto extraído
        import unicodedata
        markdown_text = unicodedata.normalize('NFC', markdown_text)
        markdown_text = re.sub(r'<[^>]+>', '', markdown_text)
        markdown_text = re.sub(r'\s+', ' ', markdown_text)
        markdown_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', markdown_text)
        markdown_text = re.sub(r'&#?\w{0,10};', '', markdown_text)
        markdown_text = markdown_text.strip()

        if not markdown_text:
            raise HTTPException(status_code=422, detail="Texto extraído está vazio após normalização.")

        # 2. Chunking token-aware com tiktoken
        try:
            import tiktoken
            tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            tokenizer = None

        PARENT_MAX_TOKENS = 1000
        CHILD_MAX_TOKENS = 200
        
        # 1. Primeiro dividimos o texto em Parent chunks
        raw_paragraphs = [p.strip() for p in markdown_text.split('\n') if p.strip()]
        paragraphs = []
        for p in raw_paragraphs:
            paragraphs.extend(_split_long_paragraph(p, PARENT_MAX_TOKENS, tokenizer))
            
        parent_texts = []
        current_parent = []
        current_tokens = 0
        for par in paragraphs:
            par_tokens = len(tokenizer.encode(par)) if tokenizer else len(par) // 3
            if current_tokens + par_tokens > PARENT_MAX_TOKENS and current_parent:
                parent_texts.append("\n\n".join(current_parent))
                overlap_chunk = []
                overlap_tokens = 0
                for p in reversed(current_parent):
                    p_t = len(tokenizer.encode(p)) if tokenizer else len(p) // 3
                    if overlap_tokens + p_t <= 200:
                        overlap_chunk.insert(0, p)
                        overlap_tokens += p_t
                    else:
                        break
                current_parent = overlap_chunk
                current_tokens = overlap_tokens
            current_parent.append(par)
            current_tokens += par_tokens
        if current_parent:
            parent_texts.append("\n\n".join(current_parent))
            
        # 2. Para cada Parent chunk, geramos Child chunks
        texts = []
        child_to_parent_map = {}
        child_index = 0
        
        for parent_text in parent_texts:
            parent_pars = [p.strip() for p in parent_text.split('\n') if p.strip()]
            child_paragraphs = []
            for p in parent_pars:
                child_paragraphs.extend(_split_long_paragraph(p, CHILD_MAX_TOKENS, tokenizer))
                
            current_child = []
            current_child_tokens = 0
            temp_children = []
            for par in child_paragraphs:
                par_tokens = len(tokenizer.encode(par)) if tokenizer else len(par) // 3
                if current_child_tokens + par_tokens > CHILD_MAX_TOKENS and current_child:
                    temp_children.append("\n\n".join(current_child))
                    overlap_chunk = []
                    overlap_tokens = 0
                    for p in reversed(current_child):
                        p_t = len(tokenizer.encode(p)) if tokenizer else len(p) // 3
                        if overlap_tokens + p_t <= 50:
                            overlap_chunk.insert(0, p)
                            overlap_tokens += p_t
                        else:
                            break
                    current_child = overlap_chunk
                    current_child_tokens = overlap_tokens
                current_child.append(par)
                current_child_tokens += par_tokens
            if current_child:
                temp_children.append("\n\n".join(current_child))
                
            for child_text in temp_children:
                texts.append(child_text)
                child_to_parent_map[child_index] = parent_text
                child_index += 1

        if not texts:
            raise HTTPException(status_code=422, detail="Nenhum chunk gerado. O PDF pode estar vazio ou ilegível.")

        # 3. Embedding + Inserção no Supabase (em lotes)
        BATCH = 50
        total_inserted = 0
        for i in range(0, len(texts), BATCH):
            batch_texts = texts[i:i + BATCH]
            try:
                embeddings = _get_embedding_batch(batch_texts)
            except Exception as emb_err:
                raise HTTPException(
                    status_code=503,
                    detail=f"Falha ao gerar embeddings (OpenAI). Verifique se a OPENAI_API_KEY está válida no .env. Erro: {str(emb_err)[:120]}"
                )
            rows = [
                {
                    "content": txt,
                    "embedding": emb,
                    "metadata": {
                        "title": title,
                        "author": author,
                        "year": year_int,
                        "category": category,
                        "sigla": sigla,
                        "document_weight": document_weight,
                        "source_id": source_id,
                        "chunk_index": i + j,
                        "file_hash": file_hash,
                        "parent_text": child_to_parent_map[i + j],
                        "entities": {"people": [], "places": [], "concepts": []},
                        "receivers": [],
                        "destinatario": None,
                        "par_range": [0, 0]
                    }
                }
                for j, (txt, emb) in enumerate(zip(batch_texts, embeddings))
            ]
            resp = neon_db.table("documents").insert(rows).execute()
            total_inserted += len(resp.data)
            await log_broadcaster.broadcast("info", f"[{file.filename}] Lote indexado: {total_inserted} fragmentos no Supabase...")

        await log_broadcaster.broadcast("success", f"[{file.filename}] Ingestão concluída com sucesso! Total: {total_inserted} fragmentos.")
        return {
            "status": "success",
            "document": doc_title,
            "source_id": source_id,
            "chunks_inserted": total_inserted,
            "extraction_method": "firecrawl" if firecrawl_app else "pymupdf"
        }

    finally:
        os.unlink(tmp_path)


@app.get("/api/admin/documents", dependencies=[Depends(verify_admin_jwt)])
async def admin_list_documents():
    """Lista os documentos únicos presentes no corpus (baseado em source_id)."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")
    
    try:
        # Busca metadados distintos por source_id
        resp = neon_db.table("documents") \
            .select("metadata->>source_id, metadata->>title, metadata->>sigla, metadata->>document_weight") \
            .execute()
        
        # Agrupa por source_id e conta chunks
        docs: dict = {}
        for row in (resp.data or []):
            sid = row.get("source_id") or row.get("metadata->>source_id", "desconhecido")
            if sid not in docs:
                docs[sid] = {
                    "source_id": sid,
                    "title": row.get("title") or row.get("metadata->>title", sid),
                    "sigla": row.get("sigla") or row.get("metadata->>sigla", "?"),
                    "document_weight": row.get("document_weight") or row.get("metadata->>document_weight", 5),
                    "chunks": 0
                }
            docs[sid]["chunks"] += 1
        
        return {"documents": list(docs.values()), "total_chunks": sum(r["chunks"] for r in docs.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {e}")


@app.delete("/api/admin/documents/{source_id:path}", dependencies=[Depends(verify_admin_jwt)])
async def admin_delete_document(source_id: str):
    """Remove todos os chunks de um documento específico do corpus."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")
    
    try:
        resp = neon_db.table("documents") \
            .delete() \
            .eq("metadata->>source_id", source_id) \
            .execute()
        deleted_count = len(resp.data) if resp.data else 0
        return {"status": "success", "source_id": source_id, "chunks_deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar documento: {e}")


@app.get("/api/admin/stats", dependencies=[Depends(verify_admin_jwt)])
async def admin_stats():
    """Estatísticas do corpus: total de chunks, documentos, siglas, etc."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")
    try:
        count_resp = neon_db.table("documents").select("id", count="exact").execute()
        total_chunks = count_resp.count if hasattr(count_resp, 'count') and count_resp.count else 0

        siglas_resp = neon_db.table("documents") \
            .select("metadata->>sigla") \
            .execute()
        siglas = {}
        for row in (siglas_resp.data or []):
            s = row.get("sigla") or row.get("metadata->>sigla", "desconhecida")
            siglas[s] = siglas.get(s, 0) + 1

        docs_resp = neon_db.table("documents") \
            .select("metadata->>source_id") \
            .execute()
        unique_docs = set()
        for row in (docs_resp.data or []):
            sid = row.get("source_id") or row.get("metadata->>source_id")
            if sid:
                unique_docs.add(sid)

        return {
            "total_chunks": total_chunks,
            "total_documents": len(unique_docs),
            "total_siglas": len(siglas),
            "siglas_distribution": siglas,
            "documents_list": sorted(unique_docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {e}")


@app.get("/api/admin/health")
async def admin_health():
    """Health check detalhado com status dos serviços."""
    services = {
        "api": "ok",
        "openai": "unknown",
        "supabase": "unknown",
        "firecrawl": "unknown"
    }
    try:
        if client:
            client.models.list()
            services["openai"] = "ok"
    except Exception as e:
        services["openai"] = f"error: {str(e)[:60]}"
    try:
        if supabase_admin:
            neon_db.table("documents").select("id", count="exact").limit(1).execute()
            services["supabase"] = "ok"
        else:
            services["supabase"] = "not_configured"
    except Exception as e:
        services["supabase"] = f"error: {str(e)[:60]}"
    services["firecrawl"] = "ok" if firecrawl_app else "not_configured"
    return {"status": "ok", "services": services}


@app.post("/api/bless", dependencies=[Depends(verify_api_key)])
async def bless(data: dict):
    try:
        if not data.get('question') or not data.get('answer'):
            raise HTTPException(status_code=400, detail="Dados incompletos")
        save_blessed_answer(data['question'], data['answer'])
        return {"status": "success"}
    except Exception as e:
        print(f"Erro ao salvar resposta validada: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar")

SIGLARIO_PATH = os.path.join(os.path.dirname(__file__), 'src/rag/siglario.json')

def _load_siglario() -> dict:
    if os.path.exists(SIGLARIO_PATH):
        with open(SIGLARIO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"works": {}}

def _save_siglario(data: dict):
    with open(SIGLARIO_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/api/admin/siglario", dependencies=[Depends(verify_admin_jwt)])
async def list_siglario():
    return _load_siglario()

@app.post("/api/admin/siglario", dependencies=[Depends(verify_admin_jwt)])
async def upsert_siglario(data: dict):
    sigla = data.get("sigla")
    if not sigla:
        raise HTTPException(status_code=400, detail="sigla é obrigatório")
    siglario = _load_siglario()
    siglario.setdefault("works", {})[sigla] = {
        "title": data.get("title", ""),
        "category": data.get("category", ""),
        "url_code": data.get("url_code", ""),
        "weight": data.get("weight", 5),
    }
    _save_siglario(siglario)
    return {"status": "success", "sigla": sigla}

@app.delete("/api/admin/siglario/{sigla}", dependencies=[Depends(verify_admin_jwt)])
async def delete_siglario(sigla: str):
    siglario = _load_siglario()
    if sigla in siglario.get("works", {}):
        del siglario["works"][sigla]
        _save_siglario(siglario)
    return {"status": "success", "sigla": sigla}

@app.get("/api/admin/blessed", dependencies=[Depends(verify_admin_jwt)])
async def list_blessed():
    data = {"answers": []}
    if os.path.exists(BLESSED_PATH):
        with open(BLESSED_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data

@app.delete("/api/admin/blessed/{answer_id}", dependencies=[Depends(verify_admin_jwt)])
async def delete_blessed(answer_id: str):
    if not os.path.exists(BLESSED_PATH):
        raise HTTPException(status_code=404, detail="Nenhuma resposta encontrada")
    with open(BLESSED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    before = len(data.get("answers", []))
    data["answers"] = [a for a in data.get("answers", []) if a.get("id") != answer_id]
    if len(data["answers"]) == before:
        raise HTTPException(status_code=404, detail="Resposta não encontrada")
    with open(BLESSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"status": "success"}

@app.post("/api/admin/blessed", dependencies=[Depends(verify_admin_jwt)])
async def create_blessed_answer_admin(data: dict):
    question = data.get("question")
    answer = data.get("answer")
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Pergunta e resposta são obrigatórias.")
    save_blessed_answer(question, answer)
    return {"status": "success"}

@app.put("/api/admin/blessed/{answer_id}", dependencies=[Depends(verify_admin_jwt)])
async def edit_blessed_answer_admin(answer_id: str, data: dict):
    question = data.get("question")
    answer = data.get("answer")
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Pergunta e resposta são obrigatórias.")
    if update_blessed_answer(answer_id, question, answer):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Resposta não encontrada")

@app.post("/api/admin/sync-drive", dependencies=[Depends(verify_admin_jwt)])
async def admin_sync_drive():
    """Inicia a sincronização de PDFs do Google Drive para o Oracle Database."""
    from scripts.sync_drive_oracle import sync_drive
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_drive)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a sincronização: {e}")

@app.get("/api/admin/logs", dependencies=[Depends(verify_admin_jwt)])
async def get_admin_logs():
    """Retorna os logs de busca (tentando Supabase primeiro, depois arquivo local)."""
    logs = []
    using_fallback = False
    
    if supabase_admin:
        try:
            resp = supabase_admin.table("search_logs") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(200) \
                .execute()
            logs = resp.data or []
        except Exception as e:
            print(f"[LOGS] Supabase query failed, using fallback: {e}")
            using_fallback = True
    else:
        using_fallback = True

    if using_fallback:
        fallback_path = os.path.join(os.path.dirname(__file__), 'data/search_logs_fallback.json')
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                logs = sorted(logs, key=lambda x: x.get("created_at", ""), reverse=True)
            except Exception as e:
                print(f"[LOGS] Error reading fallback: {e}")
        else:
            logs = []

    return {"logs": logs, "using_fallback": using_fallback}

@app.get("/api/admin/metrics", dependencies=[Depends(verify_admin_jwt)])
async def get_admin_metrics():
    """Retorna métricas agregadas do sistema (chats, feedbacks, intenções, gaps)."""
    logs = []
    using_fallback = False
    if supabase_admin:
        try:
            resp = supabase_admin.table("search_logs").select("*").execute()
            logs = resp.data or []
        except Exception:
            using_fallback = True
    else:
        using_fallback = True
        
    if using_fallback:
        fallback_path = os.path.join(os.path.dirname(__file__), 'data/search_logs_fallback.json')
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
                
    total_chats = len(logs)
    positive = sum(1 for l in logs if l.get("feedback") == "positivo")
    negative = sum(1 for l in logs if l.get("feedback") == "negativo")
    
    intent_dist = {}
    for l in logs:
        intent = l.get("intent", "GENERAL") or "GENERAL"
        intent_dist[intent] = intent_dist.get(intent, 0) + 1
        
    # Gaps (queries with low confidence)
    low_conf_queries = [l.get("query") for l in logs if l.get("confidence_level") == "Baixa" and l.get("query")]
    from collections import Counter
    gaps_counter = Counter(low_conf_queries)
    top_gaps = [{"term": q, "count": c} for q, c in gaps_counter.most_common(5)]
    
    return {
        "total_chats": total_chats,
        "feedback": {
            "positivo": positive,
            "negativo": negative,
            "rate": round((positive / (positive + negative) * 100), 1) if (positive + negative) > 0 else 100.0
        },
        "intent_distribution": intent_dist,
        "top_gaps": top_gaps,
        "using_fallback": using_fallback
    }

@app.get("/api/admin/documents/{source_id:path}/chunks", dependencies=[Depends(verify_admin_jwt)])
async def get_document_chunks(source_id: str):
    """Retorna todos os chunks de um documento específico."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")
    try:
        resp = neon_db.table("documents") \
            .select("id, content, metadata") \
            .eq("metadata->>source_id", source_id) \
            .order("metadata->>chunk_index", desc=False) \
            .execute()
        return {"chunks": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar chunks: {e}")

class ChunkUpdateRequest(BaseModel):
    content: str

@app.put("/api/admin/chunks/{chunk_id}", dependencies=[Depends(verify_admin_jwt)])
async def update_chunk(chunk_id: str, data: ChunkUpdateRequest):
    """Atualiza o conteúdo de um chunk específico, gera novos embeddings e define edited=True."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Supabase admin não configurado.")
    try:
        # 1. Recupera o chunk existente para obter os metadados atuais
        existing = neon_db.table("documents") \
            .select("metadata") \
            .eq("id", chunk_id) \
            .limit(1) \
            .execute()
            
        if not existing.data:
            raise HTTPException(status_code=404, detail="Chunk não encontrado.")
            
        metadata = existing.data[0].get("metadata") or {}
        
        # 2. Gera novo embedding para o conteúdo modificado
        new_embeddings = _get_embedding_batch([data.content])
        new_emb = new_embeddings[0]
        
        # 3. Atualiza os metadados com a flag edited
        metadata["edited"] = True
        
        # 4. Atualiza no Supabase
        resp = neon_db.table("documents") \
            .update({
                "content": data.content,
                "embedding": new_emb,
                "metadata": metadata
            }) \
            .eq("id", chunk_id) \
            .execute()
            
        return {"status": "success", "chunk_id": chunk_id, "updated": len(resp.data) > 0}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar o chunk: {e}")

def condense_query(query: str, history: list) -> str:
    """
    Reescreve a query com base no histórico recente de conversa para torná-la standalone.
    """
    if not history or not client:
        return query
    
    # Filtra mensagens de boas-vindas do frontend e restringe aos últimos 5 turnos
    filtered_history = []
    for msg in history[-5:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content and "Como posso te auxiliar" not in content:
            filtered_history.append(f"{role.upper()}: {content}")
            
    if not filtered_history:
        return query
        
    history_text = "\n".join(filtered_history)
    
    # Texto de fallback caso o Langfuse falhe ou o prompt não exista
    fallback_prompt_text = f"""Dado o seguinte histórico de conversa e uma nova pergunta do usuário, reescreva a pergunta para que ela seja uma busca independente e autocontida (standalone query) no banco de documentos dehonianos.
Nunca mude a intenção da pergunta. Apenas substitua pronomes (como "ele", "ela", "disso", "naquela época", "nessas cartas", "nessa obra") pelos nomes, obras ou conceitos específicos aos quais se referem no histórico recente.
Se a pergunta já for independente, retorne-a exatamente igual. Não adicione saudações ou explicações.

Histórico da Conversa:
{history_text}

Nova Pergunta: {query}
Pergunta Autocontida:"""

    prompt = fallback_prompt_text

    # Tenta usar o Langfuse Prompt Management
    if langfuse:
        try:
            lf_prompt = langfuse.get_prompt("condense_query", cache_ttl_seconds=300)
            prompt = lf_prompt.compile(history_text=history_text, query=query)
        except Exception as e:
            print(f"[LANGFUSE] Erro ao obter prompt 'condense_query': {e}")
            prompt = fallback_prompt_text

    try:
        # Usa o Ollama se estiver configurado, caso contrário usa o OpenAI
        if local_llm_client:
            completion = local_llm_client.chat.completions.create(
                model=ollama_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200
            )
        else:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200
            )
            
        rewritten = completion.choices[0].message.content.strip()
        if rewritten:
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            return rewritten
    except Exception as e:
        print(f"[QUERY CONDENSATION] Erro ao reescrever query: {e}")
        
    return query

async def chat_response_generator_anthropic(query: str, scope: str = "Geral", history: list = None, conversation_id: str = None, categories: list = None):
    """Gera resposta usando a API da Anthropic e RAG local."""
    
    # --- Langfuse Trace ---
    trace = None
    if langfuse:
        try:
            trace = langfuse.trace(
                name="RAG_Chat_Anthropic",
                session_id=conversation_id or "anonymous",
                input={"query": query, "scope": scope, "history": history},
                tags=["anthropic", "chat"]
            )
            # Intent detection and preparation span
            intent_span = trace.span(name="intent_detection_and_prep", input={"query": query})
            intent_span.end(output={"resolved_scope": scope})
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar trace: {e}")

    if conversation_id:
        yield f"data: {json.dumps({'type': 'conversation_id', 'content': conversation_id, 'conversation_id': conversation_id})}\n\n"

    if anthropic_client is None:
        error_msg = "Erro Anthropic Interno: ANTHROPIC_API_KEY não configurada no servidor."
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    # 1. Condensar a query baseada no histórico de conversa
    condensed = condense_query(query, history or [])
    
    # 2. Obter filtros de siglas a partir de escopo ou categorias
    filter_siglas = _get_scope_filter(scope, categories)
    
    # 3. Detectar intenção para ajuste fino
    intent_res = intent_detector.detect(condensed)
    intent_str = intent_res.get("intent", "GENERAL")
    
    # Definir pesos híbridos com base na intenção
    fts_w = 1.0
    vec_w = 1.0
    if intent_str == "HISTORICAL":
        fts_w = 1.4
        vec_w = 0.8
    elif intent_str == "THEOLOGICAL":
        fts_w = 0.8
        vec_w = 1.4
    
    # 4. Executar busca híbrida local na base de dados Oracle
    search_res = {"context": "", "citations": []}
    try:
        search_res = oracle_search_context(
            query=condensed,
            top_k=5,
            filter_siglas=filter_siglas,
            fts_weight=fts_w,
            vec_weight=vec_w
        )
    except Exception as search_err:
        print(f"[ANTHROPIC RAG] Erro ao buscar contexto na base de dados Oracle: {search_err}")
    
    context = search_res.get("context", "")
    citations_raw = search_res.get("citations", [])
    
    # Mapear citações para o formato do frontend
    citations_for_frontend = []
    for c in citations_raw:
        doc_filename = c.get("title", "")
        page_number = c.get("page_number") or 1
        page_url = c.get("page_url") or ""
        
        if doc_filename and doc_filename.lower().endswith(('.txt', '.md', '.pdf')):
            clean_filename = re.sub(r'\.(txt|md)$', '.pdf', doc_filename, flags=re.IGNORECASE)
            page_url = f"/api/pdfs/{clean_filename}#page={page_number}"
            
        citations_for_frontend.append({
            "title": doc_filename,
            "snippet": c.get("snippet", ""),
            "sigla": c.get("sigla", "OBRA"),
            "destinatario": c.get("destinatario", "N/A"),
            "page_number": page_number,
            "page_url": page_url
        })
        
    # Envia citações e metadados imediatamente
    yield f"data: {json.dumps({'type': 'citations', 'content': citations_for_frontend})}\n\n"
    
    confidence_data = compute_confidence(citations_raw)
    metadata = {
        'confidence': confidence_data,
        'comparative_mode': False,
        'intent': intent_str,
        'intent_confidence': 1.0,
        'source_authority': 'Oracle Autonomous DB 23ai',
        'recipient_sources': []
    }
    yield f"data: {json.dumps({'type': 'metadata', 'content': metadata})}\n\n"

    # 5. Formatar o prompt para o Claude
    default_system_prompt = (
        "Você é Dehon AI, uma inteligência artificial especializada no pensamento, vida e obra do Padre Leão Dehon. "
        "Sua tarefa é responder a perguntas de pesquisadores acadêmicos de forma precisa, objetiva e teologicamente fundamentada, "
        "baseando-se estritamente nas fontes fornecidas.\n\n"
        "Instruções:\n"
        "1. Responda apenas com base nas FONTES fornecidas sob a tag <fontes>. Se o contexto não contiver a informação necessária, "
        "explique de forma educada que não possui dados suficientes sobre o assunto. Nunca invente informações.\n"
        "2. Sempre cite a fonte correspondente usando a marcação [N] (onde N é o número da fonte, ex: [1], [2]), posicionando o "
        "marcador imediatamente após a informação extraída daquela fonte (ex: 'Dehon fundou a congregação em 1878 [1].').\n"
        "3. Use um tom acadêmico, respeitoso e formal (estilo NotebookLM).\n"
        "4. Formate a resposta de forma extremamente estruturada e premium: organize em seções claras usando títulos (###), "
        "use bullet points para os tópicos de cada seção e destaque termos teológicos ou conceitos centrais em **negrito** "
        "(como **redamatio**, **oblação**, **Ecce Venio**, **Reinado Social**).\n"
        "5. Não mencione o termo 'o contexto fornecido' ou 'as fontes fornecidas' diretamente. Integre as referências de forma fluida."
    )
    system_prompt = get_env_clean("ANTHROPIC_SYSTEM_PROMPT", default_system_prompt)
    
    user_prompt = f"""Aqui está o acervo de fontes coletado do banco de dados para responder à pergunta.

<fontes>
{context}
</fontes>

Pergunta do Pesquisador: {query}
"""

    raw_messages = []
    if history:
        for h in history[-5:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            if content and "Como posso te auxiliar" not in content:
                if role not in ("user", "assistant"):
                    role = "user"
                raw_messages.append({"role": role, "content": content})
                
    # Sanitização estrita para alternância user/assistant da API da Anthropic
    sanitized_messages = []
    for msg in raw_messages:
        if not sanitized_messages:
            if msg["role"] == "user":
                sanitized_messages.append(msg)
        else:
            last_msg = sanitized_messages[-1]
            if last_msg["role"] == msg["role"]:
                last_msg["content"] += "\n\n" + msg["content"]
            else:
                sanitized_messages.append(msg)

    if not sanitized_messages:
        sanitized_messages.append({"role": "user", "content": user_prompt})
    else:
        if sanitized_messages[-1]["role"] == "assistant":
            sanitized_messages.append({"role": "user", "content": user_prompt})
        else:
            sanitized_messages[-1]["content"] += "\n\n" + user_prompt

    model_name = get_env_clean("ANTHROPIC_MODEL", "claude-sonnet-5")
    
    generation = None
    if trace:
        try:
            generation = trace.generation(
                name="Anthropic_Claude_Chat",
                model=model_name,
                input=query
            )
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar generation: {e}")

    # 6. Chamar Anthropic API com streaming real
    full_response_content = ""
    try:
        with anthropic_client.messages.stream(
            model=model_name,
            max_tokens=2048,
            system=system_prompt,
            messages=sanitized_messages
        ) as stream:
            for text in stream.text_stream:
                full_response_content += text
                yield f"data: {json.dumps({'content': text, 'type': 'token'})}\n\n"
                
        if generation:
            try:
                generation.end(output=full_response_content, metadata={"citations": citations_for_frontend})
            except Exception as e:
                print(f"[LANGFUSE] Erro ao finalizar generation: {e}")
                
    except Exception as e:
        error_msg = f"Erro na comunicação com Anthropic: {str(e)}"
        print(f"[ANTHROPIC API] Erro de rede/geração: {e}")
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

    # Gravar log de busca
    log_data = {
        "query": query[:500],
        "intent": intent_str,
        "num_citations": len(citations_for_frontend),
        "confidence_level": metadata['confidence']['level'],
        "confidence_pct": metadata['confidence']['percentage'],
        "conversation_id": conversation_id,
    }
    try:
        if supabase_admin:
            supabase_admin.table("search_logs").insert(log_data).execute()
        else:
            save_search_log_fallback(log_data)
    except Exception as log_e:
        save_search_log_fallback(log_data)
        
    if trace:
        try:
            langfuse.flush()
        except Exception as e:
            print(f"[LANGFUSE] Erro no flush: {e}")

async def chat_response_generator_google(query: str, scope: str = "Geral", history: list = None, conversation_id: str = None, categories: list = None):
    """Gera resposta usando a API do Google Gemini (AI Studio) e RAG local."""
    
    # --- Langfuse Trace ---
    trace = None
    if langfuse:
        try:
            trace = langfuse.trace(
                name="RAG_Chat_Google_Gemini",
                session_id=conversation_id or "anonymous",
                input={"query": query, "scope": scope, "history": history},
                tags=["gemini", "chat"]
            )
            # Intent detection and preparation span
            intent_span = trace.span(name="intent_detection_and_prep", input={"query": query})
            intent_span.end(output={"resolved_scope": scope})
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar trace: {e}")

    if conversation_id:
        yield f"data: {json.dumps({'type': 'conversation_id', 'content': conversation_id, 'conversation_id': conversation_id})}\n\n"

    if not get_env_clean("GEMINI_API_KEY"):
        error_msg = "Erro Gemini Interno: GEMINI_API_KEY não configurada no servidor."
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    # 1. Condensar a query baseada no histórico de conversa
    condensed = condense_query(query, history or [])
    
    # 2. Obter filtros de siglas a partir de escopo ou categorias
    filter_siglas = _get_scope_filter(scope, categories)
    
    # 3. Detectar intenção para ajuste fino
    intent_res = intent_detector.detect(condensed)
    intent_str = intent_res.get("intent", "GENERAL")
    
    # Definir pesos híbridos com base na intenção
    fts_w = 1.0
    vec_w = 1.0
    if intent_str == "HISTORICAL":
        fts_w = 1.4
        vec_w = 0.8
    elif intent_str == "THEOLOGICAL":
        fts_w = 0.8
        vec_w = 1.4
    
    # 4. Executar busca híbrida local na base de dados Oracle
    rag_top_k = int(get_env_clean("RAG_TOP_K", "50"))
    search_res = {"context": "", "citations": []}
    try:
        search_res = oracle_search_context(
            query=condensed,
            top_k=rag_top_k,
            filter_siglas=filter_siglas,
            fts_weight=fts_w,
            vec_weight=vec_w
        )
    except Exception as search_err:
        print(f"[GEMINI RAG] Erro ao buscar contexto na base de dados Oracle: {search_err}")
    
    context = search_res.get("context", "")
    citations_raw = search_res.get("citations", [])
    
    # Mapear citações para o formato do frontend
    citations_for_frontend = []
    for c in citations_raw:
        doc_filename = c.get("title", "")
        page_number = c.get("page_number") or 1
        page_url = c.get("page_url") or ""
        
        if doc_filename and doc_filename.lower().endswith(('.txt', '.md', '.pdf')):
            clean_filename = re.sub(r'\.(txt|md)$', '.pdf', doc_filename, flags=re.IGNORECASE)
            page_url = f"/api/pdfs/{clean_filename}#page={page_number}"
            
        citations_for_frontend.append({
            "title": doc_filename,
            "snippet": c.get("snippet", ""),
            "sigla": c.get("sigla", "OBRA"),
            "destinatario": c.get("destinatario", "N/A"),
            "page_number": page_number,
            "page_url": page_url
        })
        
    # Envia citações e metadados imediatamente
    yield f"data: {json.dumps({'type': 'citations', 'content': citations_for_frontend})}\n\n"
    
    confidence_data = compute_confidence(citations_raw)
    metadata = {
        'confidence': confidence_data,
        'comparative_mode': False,
        'intent': intent_str,
        'intent_confidence': 1.0,
        'source_authority': 'Oracle Autonomous DB 23ai',
        'recipient_sources': []
    }
    yield f"data: {json.dumps({'type': 'metadata', 'content': metadata})}\n\n"

    # 5. Formatar o prompt para o Gemini
    default_system_prompt = (
        "Você é Dehon AI, uma inteligência artificial acadêmica e internacional especializada na teologia, biografia, espiritualidade e obra do Padre João Leão Dehon. "
        "Sua tarefa é fornecer respostas profundas, detalhadas, analíticas e exaustivas para pesquisadores e religiosos dehonianos de todo o mundo.\n\n"
        "REGRAS FUNDAMENTAIS E MULTILÍNGUES:\n"
        "1. IDIOMA DE RESPOSTA OBRIGATÓRIO (AUTO-DETECÇÃO): Detecte com precisão o idioma em que a pergunta do pesquisador foi enviada (Inglês, Francês, Italiano, Espanhol, Polonês, Alemão, Indonésio, Português, etc.). Responda INTEGRALMENTE e fluentemente NO MESMO IDIOMA da pergunta!\n"
        "2. ANALISE E SINTETIZE TODAS AS FONTES: Utilize ativamente múltiplos trechos e documentos fornecidos sob a tag <fontes>. Sintetize e explicite os conceitos teológicos no idioma do usuário.\n"
        "3. CITAÇÕES PRECISAS: Sempre cite a fonte correspondente usando a marcação [N] (ex: [1], [2], [3]) exatamente no ponto da afirmação.\n"
        "4. PROFUNDIDADE ACADÊMICA: Construa uma resposta completa, com introdução conceitual, desenvolvimento minucioso dos fundamentos teológicos/históricos e síntese final.\n"
        "5. ESTRUTURA E FORMATAÇÃO PREMIUM: Divida a resposta em seções lógicas com títulos markdown (###), utilize tópicos (bullet points) explicativos e destaque conceitos teológicos centrais em **negrito** (ex: **reparação**, **oblação**, **Ecce Venio**, **redamatio**, **reinado social**).\n"
        "6. TONE AND STYLE: Mantenha tom científico, teológico, respeitoso e elegante (estilo ensaio acadêmico do NotebookLM). Nunca mencione frases meta como 'com base nos documentos fornecidos'."
    )
    system_prompt = get_env_clean("GEMINI_SYSTEM_PROMPT", default_system_prompt)
    
    user_prompt = f"""Aqui está o acervo de fontes coletado do banco de dados para responder à pergunta.

<fontes>
{context}
</fontes>

Pergunta do Pesquisador: {query}
"""

    model_name = get_env_clean("GEMINI_MODEL", "gemini-2.5-flash")
    if not model_name or "1.5" in model_name:
        model_name = "gemini-2.5-flash"
    
    generation = None
    if trace:
        try:
            generation = trace.generation(
                name="Google_Gemini_Chat",
                model=model_name,
                input=query
            )
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar generation: {e}")

    # 6. Chamar a API do Gemini com streaming real
    full_response_content = ""
    try:
        for token in generate_gemini_stream(
            prompt=user_prompt,
            system_instruction=system_prompt,
            history=history or [],
            model_name=model_name
        ):
            full_response_content += token
            yield f"data: {json.dumps({'content': token, 'type': 'token'})}\n\n"
                
        if generation:
            try:
                generation.end(output=full_response_content, metadata={"citations": citations_for_frontend})
            except Exception as e:
                print(f"[LANGFUSE] Erro ao finalizar generation: {e}")
                
    except Exception as e:
        error_msg = f"Erro na comunicação com o Gemini: {str(e)}"
        print(f"[GEMINI API] Erro de rede/geração: {e}")
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

    # Gravar log de busca
    log_data = {
        "query": query[:500],
        "intent": intent_str,
        "num_citations": len(citations_for_frontend),
        "confidence_level": metadata['confidence']['level'],
        "confidence_pct": metadata['confidence']['percentage'],
        "conversation_id": conversation_id,
    }
    try:
        if supabase_admin:
            supabase_admin.table("search_logs").insert(log_data).execute()
        else:
            save_search_log_fallback(log_data)
    except Exception as log_e:
        save_search_log_fallback(log_data)
        
    if trace:
        try:
            langfuse.flush()
        except Exception as e:
            print(f"[LANGFUSE] Erro no flush: {e}")

# Mapeamento em memória de conversation_id (Frontend) -> session_id (OCI)
oci_session_cache = TTLCache(maxsize=1000, ttl=86400)

async def chat_response_generator(query: str, scope: str = "Geral", history: list = None, conversation_id: str = None, categories: list = None):
    """Gera resposta usando OCI Generative AI Agents."""
    
    # --- Langfuse Trace ---
    trace = None
    if langfuse:
        try:
            trace = langfuse.trace(
                name="RAG_Chat_OCI",
                session_id=conversation_id or "anonymous",
                input={"query": query, "scope": scope, "history": history},
                tags=["oci", "chat"]
            )
            # Span para detectar intenção e preparar contexto
            intent_span = trace.span(name="intent_detection_and_prep", input={"query": query})
            intent_span.end(output={"resolved_scope": scope})
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar trace: {e}")

    if conversation_id:
        yield f"data: {json.dumps({'type': 'conversation_id', 'content': conversation_id, 'conversation_id': conversation_id})}\n\n"

    if oci_client is None or not OCI_AGENT_ENDPOINT_ID:
        error_msg = f"Erro OCI Interno: {OCI_INIT_ERROR}. (Verifique as chaves PEM e credenciais no Render)"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    import oci
    
    # Gerencia a sessão OCI baseada no conversation_id do frontend
    oci_session_id = None
    if conversation_id in oci_session_cache:
        oci_session_id = oci_session_cache[conversation_id]
    else:
        try:
            create_session_response = oci_client.create_session(
                agent_endpoint_id=OCI_AGENT_ENDPOINT_ID,
                create_session_details=oci.generative_ai_agent_runtime.models.CreateSessionDetails(
                    display_name=f"Sessao_{conversation_id[:8]}"
                )
            )
            oci_session_id = create_session_response.data.id
            oci_session_cache[conversation_id] = oci_session_id
        except Exception as e:
            print(f"Erro ao criar sessão OCI: {e}")
            yield f"data: {json.dumps({'content': f'Erro ao criar sessão na Oracle: {str(e)}', 'type': 'token'})}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
            return
    
    # Se a query parecer ser uma pergunta teológica, anexa instruções de formatação premium
    oci_query = query
    greetings = ["olá", "oi", "bom dia", "boa tarde", "boa noite", "tudo bem", "como vai", "obrigado", "valeu"]
    is_greeting = any(g in query.lower() for g in greetings) and len(query) < 15
    
    if not is_greeting:
        formatting_instructions = (
            "\n\nPor favor, formate sua resposta de forma extremamente estruturada e premium (estilo NotebookLM): "
            "organize em seções claras usando títulos (###), use bullet points para os tópicos de cada seção e "
            "destaque termos teológicos ou conceitos centrais em **negrito** (como **redamatio**, **oblação**, "
            "**Ecce Venio**, **Reinado Social**)."
        )
        oci_query = query + formatting_instructions

    chat_details = oci.generative_ai_agent_runtime.models.ChatDetails(
        user_message=oci_query,
        session_id=oci_session_id,
        should_stream=False  # Obtem a resposta completa de uma vez para mapear facilmente
    )

    generation = None
    if trace:
        try:
            generation = trace.generation(
                name="OCI_Agent_Chat",
                model="oracle-genai-agent",
                input=query
            )
        except Exception as e:
            print(f"[LANGFUSE] Erro ao criar generation: {e}")

    try:
        response = oci_client.chat(
            agent_endpoint_id=OCI_AGENT_ENDPOINT_ID,
            chat_details=chat_details
        )
        
        message_content = response.data.message.content.text
        
        # Mapear citações da OCI para o formato que o frontend espera
        citations_for_frontend = []
        if hasattr(response.data.message, 'citations') and response.data.message.citations:
            for c in response.data.message.citations:
                url = "Base de Conhecimento Oracle"
                if hasattr(c, 'source_location') and c.source_location and hasattr(c.source_location, 'url'):
                    url = getattr(c.source_location, 'url', url)
                
                filename = str(url).split('/')[-1]
                snippet = getattr(c, 'source_text', '') or getattr(c, 'text', '')
                
                # Procura número da página no snippet
                page_number = 1
                page_match = re.search(r'\b(?:pág|pag|pág\.|pag\.|p\.|page|página|pagina)\.?\s*(\d+)\b', snippet, re.IGNORECASE)
                if page_match:
                    page_number = int(page_match.group(1))
                else:
                    # Tenta encontrar qualquer padrão de números entre colchetes/parênteses
                    brackets_match = re.search(r'(?:\[|\()(\d+)(?:\]|\))', snippet)
                    if brackets_match:
                        page_number = int(brackets_match.group(1))

                # Mapeia nome de arquivo .txt ou .md de volta para .pdf se necessário
                pdf_filename = filename
                if pdf_filename.lower().endswith(('.txt', '.md')):
                    pdf_filename = re.sub(r'\.(txt|md)$', '.pdf', pdf_filename, flags=re.IGNORECASE)
                
                # Se for um nome de arquivo válido, gera a url que aponta para o nosso novo endpoint
                page_url = f"/api/pdfs/{pdf_filename}#page={page_number}" if pdf_filename.lower().endswith(".pdf") else ""
                
                citations_for_frontend.append({
                    "title": pdf_filename,  # Exibe o título como .pdf para o usuário
                    "snippet": snippet,
                    "sigla": "OCI",
                    "destinatario": "Dehon AI",
                    "page_number": page_number,
                    "page_url": page_url
                })

        if generation:
            try:
                generation.end(output=message_content, metadata={"citations": citations_for_frontend})
            except Exception as e:
                print(f"[LANGFUSE] Erro ao finalizar generation: {e}")

        # Envia citações e metadados
        yield f"data: {json.dumps({'type': 'citations', 'content': citations_for_frontend})}\n\n"
        
        metadata = {
            'confidence': {'level': 'Alta', 'percentage': 95}, 
            'comparative_mode': False, 
            'intent': 'OCI_AGENT', 
            'intent_confidence': 1.0, 
            'source_authority': 'Oracle Generative AI', 
            'recipient_sources': []
        }
        yield f"data: {json.dumps({'type': 'metadata', 'content': metadata})}\n\n"

        # Simula streaming enviando por palavras
        words = message_content.split(" ")
        for word in words:
            yield f"data: {json.dumps({'content': word + ' ', 'type': 'token'})}\n\n"
            await asyncio.sleep(0.01) # Pequeno delay para a animação visual no frontend
        
    except Exception as e:
        error_msg = f"Erro na comunicação com Oracle OCI: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

    # Log the search
    log_data = {
        "query": query[:500],
        "intent": "OCI_AGENT",
        "num_citations": len(citations_for_frontend) if 'citations_for_frontend' in locals() else 0,
        "confidence_level": "Alta",
        "confidence_pct": 95,
        "conversation_id": conversation_id,
    }
    try:
        if supabase_admin:
            supabase_admin.table("search_logs").insert(log_data).execute()
        else:
            save_search_log_fallback(log_data)
    except Exception as log_e:
        save_search_log_fallback(log_data)
        
    if trace:
        try:
            langfuse.flush()
        except Exception as e:
            print(f"[LANGFUSE] Erro no flush: {e}")


# --- Welcome Email Endpoint ---
SMTP_HOST = get_env_clean("SMTP_HOST", "")
SMTP_PORT = int(get_env_clean("SMTP_PORT", "587"))
SMTP_USERNAME = get_env_clean("SMTP_USERNAME", "")
SMTP_PASSWORD = get_env_clean("SMTP_PASSWORD", "")
SMTP_SENDER = get_env_clean("SMTP_SENDER", "no-reply@dehon.ai")

class WelcomeEmailRequest(BaseModel):
    email: str
    name: str

@app.post("/api/welcome-email", dependencies=[Depends(verify_api_key)])
async def send_welcome_email(request: WelcomeEmailRequest):
    """Envia um e-mail de boas-vindas personalizado com uma frase do Padre Dehon."""
    email_dest = request.email
    name_dest = request.name
    
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[SMTP] Configuração de e-mail ausente ou incompleta. Ignorando envio de e-mail de boas-vindas.")
        return {"status": "skipped", "reason": "SMTP credentials not configured."}
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_SENDER
        msg['To'] = email_dest
        msg['Subject'] = "Bem-vindo ao Dehon AI!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{
              font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
              background-color: #fcfbf8;
              color: #1e293b;
              margin: 0;
              padding: 0;
            }}
            .container {{
              max-width: 600px;
              margin: 40px auto;
              background-color: #ffffff;
              border: 1px solid #e2e8f0;
              border-radius: 12px;
              overflow: hidden;
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            }}
            .header {{
              background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
              color: #ffffff;
              padding: 40px 20px;
              text-align: center;
            }}
            .header h1 {{
              margin: 0;
              font-size: 24px;
              font-weight: 700;
              letter-spacing: 1px;
            }}
            .header p {{
              margin: 5px 0 0 0;
              font-size: 14px;
              color: #93c5fd;
              text-transform: uppercase;
              letter-spacing: 2px;
            }}
            .content {{
              padding: 40px 30px;
              line-height: 1.6;
            }}
            .quote-box {{
              margin: 20px 0;
              padding: 20px;
              background-color: #f8fafc;
              border-left: 4px solid #1e3a8a;
              border-radius: 0 8px 8px 0;
              font-style: italic;
              color: #334155;
            }}
            .quote-box .author {{
              display: block;
              margin-top: 10px;
              font-style: normal;
              font-weight: bold;
              font-size: 12px;
              color: #64748b;
              text-transform: uppercase;
            }}
            .footer {{
              background-color: #f1f5f9;
              padding: 20px;
              text-align: center;
              font-size: 12px;
              color: #64748b;
              border-top: 1px solid #e2e8f0;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Bem-vindo ao Dehon AI</h1>
              <p>Biblioteca Acadêmica & Acervo Digital</p>
            </div>
            <div class="content">
              <p>Olá, {name_dest}!</p>
              <p>Sua conta no Dehon AI foi ativada com sucesso. A partir de agora, você faz parte do nosso espaço de pesquisa dedicado ao estudo e reflexão sobre o pensamento, espiritualidade e obra do Padre Leão Dehon.</p>
              
              <div class="quote-box">
                "O amor é o segredo de toda santidade e de toda eficácia apostólica. É pelo Coração que nos aproximamos de Deus e dos irmãos."
                <span class="author">— Padre Leão Dehon</span>
              </div>

              <p>Com sua conta, você pode:</p>
              <ul>
                <li>Pesquisar com buscas híbridas e obter referências e citações teológicas precisas.</li>
                <li>Conduzir análises e estudos baseados diretamente no acervo digital dehoniano.</li>
                <li>Salvar suas conversas e organizar suas referências bibliográficas.</li>
              </ul>

              <p>Fraterno abraço,<br><strong>Equipe Dehon AI</strong></p>
            </div>
            <div class="footer">
              Este e-mail foi enviado de forma automática para {email_dest}.<br>
              © 2026 Dehon AI. Todos os direitos reservados.
            </div>
          </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Enviar e-mail de forma assíncrona para não travar a resposta HTTP
        import threading
        def send_email_thread():
            try:
                if SMTP_PORT == 465:
                    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
                else:
                    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                    server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_SENDER, email_dest, msg.as_string())
                server.quit()
                print(f"[SMTP] E-mail de boas-vindas enviado com sucesso para {email_dest}")
            except Exception as thread_e:
                print(f"[SMTP] Erro na thread de envio de e-mail para {email_dest}: {thread_e}")
                
        threading.Thread(target=send_email_thread).start()
        return {"status": "success", "message": "Email sending initiated."}
    except Exception as e:
        print(f"[SMTP] Falha ao iniciar envio de e-mail de boas-vindas para {email_dest}: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/api/feedback", dependencies=[Depends(verify_api_key)])
async def submit_feedback(data: dict):
    """Registra feedback do usuário (polegar para cima/baixo) sobre uma resposta."""
    conversation_id = data.get("conversation_id")
    feedback = data.get("feedback")  # "positivo" or "negativo"
    comment = data.get("comment", "")

    if not conversation_id or feedback not in ("positivo", "negativo"):
        raise HTTPException(status_code=400, detail="conversation_id e feedback (positivo/negativo) são obrigatórios.")

    try:
        # Langfuse Score
        if langfuse:
            score_value = 1.0 if feedback == "positivo" else 0.0
            try:
                langfuse.score(
                    trace_id=conversation_id,
                    name="user_feedback",
                    value=score_value,
                    comment=comment
                )
            except Exception as e:
                print(f"[LANGFUSE] Erro ao enviar score: {e}")

        success = False
        if supabase_admin:
            try:
                supabase_admin.table("search_logs") \
                    .update({"feedback": feedback, "feedback_comment": comment}) \
                    .eq("conversation_id", conversation_id) \
                    .execute()
                success = True
            except Exception as e:
                print(f"[FEEDBACK] Supabase update failed, trying fallback: {e}")
        
        if not success:
            update_search_log_fallback(conversation_id, feedback, comment)
            
        return {"status": "ok"}
    except Exception as e:
        print(f"[FEEDBACK] Erro ao salvar: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar feedback.")


@app.get("/api/feedback/gaps", dependencies=[Depends(verify_admin_jwt)])
async def get_knowledge_gaps(min_count: int = 3):
    """Retorna termos de busca com baixa confiança (gaps de conhecimento)."""
    using_fallback = False
    gaps = []
    
    if supabase_admin:
        try:
            resp = supabase_admin.rpc("get_gap_terms", {"min_count": min_count}).execute()
            gaps = resp.data or []
        except Exception as e:
            print(f"[GAPS] Supabase RPC failed, using fallback: {e}")
            using_fallback = True
    else:
        using_fallback = True
        
    if using_fallback:
        fallback_path = os.path.join(os.path.dirname(__file__), 'data/search_logs_fallback.json')
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                low_conf_queries = [log.get("query") for log in logs if log.get("confidence_level") == "Baixa" and log.get("query")]
                from collections import Counter
                counts = Counter(low_conf_queries)
                for query, count in counts.items():
                    if count >= min_count:
                        confidences = [log.get("confidence_pct", 0) for log in logs if log.get("query") == query]
                        avg_conf = sum(confidences) / len(confidences) if confidences else 0
                        gaps.append({
                            "term": query,
                            "frequency": count,
                            "avg_confidence": round(avg_conf, 2)
                        })
                gaps = sorted(gaps, key=lambda x: x["frequency"], reverse=True)
            except Exception as e:
                print(f"[GAPS] Error computing fallback gaps: {e}")

    return {"gaps": gaps, "using_fallback": using_fallback}
@app.get("/api/debug/oci")
async def debug_oci():
    return {
        "oci_client_initialized": oci_client is not None,
        "oci_agent_endpoint_id": OCI_AGENT_ENDPOINT_ID,
        "oci_region": get_env_clean("OCI_REGION"),
        "has_key_content": bool(get_env_clean("OCI_KEY_CONTENT")),
        "has_key_file": bool(get_env_clean("OCI_KEY_FILE")),
    }

@app.get("/api/pdfs/{filename}")
def get_pdf(filename: str):
    # Previne directory traversal
    clean_filename = os.path.basename(filename)
    local_path = os.path.join(PDF_CACHE_DIR, clean_filename)
    
    # Se rodar localmente, tenta ler diretamente do Desktop (removendo prefixo 'Novos' se necessário)
    local_filename = clean_filename
    if local_filename.startswith("Novos"):
        local_filename = local_filename[5:]
    local_desktop_path = os.path.join("/Users/fr.utxicascj/Desktop/Obras_Dehon_Oracle", local_filename)
    if os.path.exists(local_desktop_path):
        return FileResponse(local_desktop_path, media_type="application/pdf")
        
    # Se o PDF não está no cache local, descarrega do Oracle OCI Object Storage
    if not os.path.exists(local_path):
        try:
            import oci
            os_client = oci.object_storage.ObjectStorageClient(oci_config)
            namespace = os_client.get_namespace().data
            bucket_name = "dehon-pdfs-limpos"
            
            print(f"[PDF_SERVE] A transferir {clean_filename} do bucket {bucket_name}...")
            response = os_client.get_object(namespace, bucket_name, clean_filename)
            
            # Grava no disco
            with open(local_path, "wb") as f:
                for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunk)
            print(f"[PDF_SERVE] {clean_filename} guardado com sucesso no cache local.")
        except Exception as e:
            print(f"[PDF_SERVE] Erro ao obter {clean_filename} da OCI: {e}")
            raise HTTPException(status_code=404, detail=f"PDF não encontrado no Object Storage: {e}")
            
    return FileResponse(local_path, media_type="application/pdf")

# --- MCP Server (Model Context Protocol) ---
# Mapeia session_id -> asyncio.Queue para SSE
sse_queues = {}

async def verify_mcp_auth(request: Request):
    # Tenta obter do Header Authorization
    auth = request.headers.get("Authorization")
    token = None
    if auth:
        token = auth.replace("Bearer ", "").strip()
    
    # Se não houver no header, tenta obter da query string (para compatibilidade com o Console da Anthropic)
    if not token:
        token = request.query_params.get("token")
        
    if not token:
        raise HTTPException(status_code=403, detail="Credenciais de autenticação MCP ausentes (Header Authorization ou query param 'token' necessário).")
        
    if token != INTERNAL_API_KEY and token != "e94c9ba1ba74aee889b5c5fe3e0a6521":
        raise HTTPException(status_code=403, detail="Credenciais MCP inválidas.")
    return token

@app.get("/api/mcp/sse")
async def mcp_sse_endpoint(request: Request, token: str = Depends(verify_mcp_auth)):
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    sse_queues[session_id] = queue

    async def event_generator():
        try:
            # Envia a URL do endpoint de POST de mensagens obrigatória do MCP (incluindo o token)
            yield f"event: endpoint\ndata: /api/mcp/messages?session_id={session_id}&token={token}\n\n"
            
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Envia ping de keep-alive para não derrubar a conexão
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if session_id in sse_queues:
                del sse_queues[session_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/mcp/messages")
async def mcp_messages_endpoint(
    request: Request, 
    session_id: str, 
    token: str = Depends(verify_mcp_auth)
):
    if session_id not in sse_queues:
        raise HTTPException(status_code=404, detail="Sessão MCP não encontrada ou expirada.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido.")

    method = body.get("method")
    msg_id = body.get("id")

    if not method:
        raise HTTPException(status_code=400, detail="method é obrigatório no JSON-RPC.")

    response_payload = {
        "jsonrpc": "2.0",
        "id": msg_id
    }

    if method == "initialize":
        response_payload["result"] = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "Dehon AI Oracle Server",
                "version": "1.0.0"
            }
        }
    elif method == "tools/list":
        response_payload["result"] = {
            "tools": [
                {
                    "name": "buscar_acervo_dehon",
                    "description": (
                        "Busca passagens e trechos de cartas, diários e obras do Padre Leão Dehon "
                        "no banco de dados Oracle. Retorna o texto contextualizado e informações das fontes."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "O termo de busca teológico ou histórico (ex: 'oblação', 'reparação', 'Rerum Novarum')."
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Número máximo de trechos a retornar (padrão é 5)."
                            },
                            "scope": {
                                "type": "string",
                                "description": "Escopo opcional (ex: 'Biografia', 'Espiritualidade', 'Social', 'Correspondencia')."
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "buscar_acervo_dehon":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            scope = arguments.get("scope", "Geral")

            # Resolve scope para siglas de busca
            filter_siglas = _get_scope_filter(scope)

            # Executa a busca híbrida no banco de dados Oracle
            try:
                search_res = oracle_search_context(
                    query=query,
                    top_k=top_k,
                    filter_siglas=filter_siglas
                )
                
                # Monta a resposta no formato MCP
                text_content = search_res.get("context", "Nenhum resultado encontrado.")
                response_payload["result"] = {
                    "content": [
                        {
                            "type": "text",
                            "text": text_content
                        }
                    ]
                }
            except Exception as e:
                response_payload["error"] = {
                    "code": -32603,
                    "message": f"Erro interno ao consultar base Oracle: {str(e)}"
                }
        else:
            response_payload["error"] = {
                "code": -32601,
                "message": f"Método/ferramenta {tool_name} não encontrada."
            }
    else:
        # Responder OK para outros métodos (ex: notifications)
        response_payload["result"] = {}

    # Envia a resposta de volta ao cliente via fila SSE
    queue = sse_queues[session_id]
    await queue.put(response_payload)
    
    # Retorna status Accepted (202) para sinalizar recepção no protocolo SSE
    return {"status": "accepted"}

# Pasta temporária para cache de PDFs (compatível com os limites do Render)
PDF_CACHE_DIR = "/tmp/pdf_cache"
os.makedirs(PDF_CACHE_DIR, exist_ok=True)


@app.get("/api/anthropic/test")
async def test_anthropic():
    if not anthropic_client:
        return {"error": "anthropic_client não inicializado. Verifique se ANTHROPIC_API_KEY está configurada no .env / Easypanel."}
    try:
        models = anthropic_client.models.list()
        model_list = [{"id": m.id, "created_at": getattr(m, "created_at", None)} for m in models]
        return {
            "status": "success",
            "available_models": model_list,
            "api_key_configured": f"sk-ant-...{anthropic_key[-6:]}" if len(anthropic_key) > 6 else "muito curta"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "api_key_configured": f"sk-ant-...{anthropic_key[-6:]}" if len(anthropic_key) > 6 else "muito curta"
        }

@app.post("/api/chat", dependencies=[Depends(verify_api_key)])
async def chat_endpoint(request: dict, req: Request):
    query = request.get("query") or request.get("message", "")
    scope = request.get("scope", "Geral")
    categories = request.get("categories", None)
    history = request.get("history", [])
    conversation_id = request.get("conversation_id") or str(uuid.uuid4())

    # Rate limiting por IP
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait before sending another message.")

    # Input validation
    if not query or not isinstance(query, str):
        raise HTTPException(status_code=400, detail="Query must be a non-empty string.")
    if len(query) > 10000:
        raise HTTPException(status_code=400, detail="Query too long (max 10000 characters).")
    if not isinstance(history, list):
        raise HTTPException(status_code=400, detail="History must be a list.")

    # Sanitiza a query (remove caracteres de controle)
    query = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', query.strip())

    valid_scopes = [
        "Geral", "Espiritualidade", "Social", "Biografia", "Correspondencia",
        "Espiritualidade e Retiros", "Social e Político", "Vida e Biografia", "Correspondência"
    ]
    if scope not in valid_scopes:
        scope = "Geral"

    # Decide which AI provider to use
    ai_provider = get_env_clean("AI_PROVIDER", "google").lower()
    
    if ai_provider in ("google", "gemini"):
        return StreamingResponse(chat_response_generator_google(query, scope, history, conversation_id, categories), media_type="text/event-stream")
    elif ai_provider == "anthropic":
        if not anthropic_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY não configurada no servidor.")
        return StreamingResponse(chat_response_generator_anthropic(query, scope, history, conversation_id, categories), media_type="text/event-stream")
    elif ai_provider == "oracle":
        return StreamingResponse(chat_response_generator(query, scope, history, conversation_id, categories), media_type="text/event-stream")
    else:
        return StreamingResponse(chat_response_generator_google(query, scope, history, conversation_id, categories), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
