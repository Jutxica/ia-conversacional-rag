import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Generator

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def format_history_to_gemini(history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Formata o histórico de mensagens do padrão OpenAI/Anthropic (role: user/assistant)
    para o formato do Google Gemini (role: user/model) e garante a alternância obrigatória de turnos.
    """
    gemini_history = []
    for h in history:
        role = h.get("role", "user")
        content = h.get("content", "")
        if not content:
            continue
            
        if role == "assistant":
            role = "model"
        else:
            role = "user"
            
        # Garante alternância: se o último item inserido tiver o mesmo papel, junta o texto
        if gemini_history and gemini_history[-1]["role"] == role:
            gemini_history[-1]["parts"][0]["text"] += "\n\n" + content
        else:
            gemini_history.append({
                "role": role,
                "parts": [{"text": content}]
            })
    return gemini_history

def generate_gemini_stream(
    prompt: str,
    system_instruction: str = None,
    history: List[Dict[str, str]] = None,
    model_name: str = "gemini-1.5-flash"
) -> Generator[str, None, None]:
    """
    Gera tokens via streaming usando a API do Google Gemini.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada no ambiente.")
        
    # Inicializa o modelo com instrução do sistema opcional
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction
    )
    
    # Se houver histórico de mensagens anterior, inicia sessão de chat
    if history:
        gemini_history = format_history_to_gemini(history)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(prompt, stream=True)
    else:
        response = model.generate_content(prompt, stream=True)
        
    for chunk in response:
        try:
            if chunk.text:
                yield chunk.text
        except Exception as e:
            # Se for bloqueado por segurança ou erro de parte sem texto, apenas ignore silenciosamente
            print(f"[GEMINI CLIENT] Aviso ao extrair bloco de streaming: {e}")

def analyze_text_entities_and_sentiment_gemini(text: str) -> Dict[str, Any]:
    """
    Utiliza o Gemini 1.5 Flash de forma gratuita no AI Studio para realizar processamento
    de linguagem natural (NLU) em fragmentos de obras, extraindo entidades e sentimento.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada no ambiente.")
        
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Você é um assistente de Processamento de Linguagem Natural especializado em análise teológica e histórica.
    Sua tarefa é analisar o seguinte fragmento de texto de uma obra teológica ou carta histórica e extrair:
    1. Entidades relevantes:
       - Pessoas (especialmente santos, papas, padres ou figuras citadas pelo Padre Dehon)
       - Locais (cidades, países, locais de retiros ou eventos importantes)
       - Datas ou períodos de tempo
       - Organizações ou congregações
       - Conceitos teológicos centrais (ex: oblação, reparação, reinado social, etc.)
    2. Sentimento geral do texto:
       - Um score de sentimento entre -1.0 (muito triste, aflito, negativo) e 1.0 (muito alegre, esperançoso, positivo).
       - Uma label de classificação ("POSITIVE", "NEGATIVE", "NEUTRAL").

    Retorne APENAS um objeto JSON válido, sem tags de markdown, com a seguinte estrutura:
    {{
      "entities": [
        {{
          "name": "nome da entidade",
          "type": "PERSON" ou "LOCATION" ou "DATE" ou "ORGANIZATION" ou "THEOLOGICAL_CONCEPT",
          "explanation": "breve explicação contextual do porquê esta entidade foi citada"
        }}
      ],
      "sentiment": {{
        "score": 0.0,
        "label": "POSITIVE" ou "NEGATIVE" ou "NEUTRAL"
      }}
    }}

    Fragmento de texto para analisar:
    ---
    {text}
    ---
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"[GEMINI NLU] Erro ao processar texto com Gemini: {e}")
        return {"entities": [], "sentiment": {"score": 0.0, "label": "NEUTRAL"}}
