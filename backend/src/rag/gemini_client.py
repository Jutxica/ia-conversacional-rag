import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Generator

def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "").strip('"').strip("'").strip()
    if api_key:
        genai.configure(api_key=api_key)
    return api_key

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
    model_name: str = "gemini-2.5-flash"
) -> Generator[str, None, None]:
    """
    Gera tokens via streaming usando a API do Google Gemini.
    """
    api_key = configure_gemini()
    if not api_key:
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
    api_key = configure_gemini()
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada no ambiente.")
        
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    Você é um historiador especialista na vida, cartas e obras do Padre João Leão Dehon (fundador dos Dehonianos/Sacerdotes do Sagrado Coração de Jesus - SCJ) e um assistente especialista de Processamento de Linguagem Natural.
    
    Sua tarefa é analisar minuciosamente o fragmento de texto fornecido (que pode ser uma carta, diário espiritual ou tratado teológico) e extrair TODAS as entidades teológicas, históricas, espirituais e institucionais relevantes. Seja extremamente minucioso e não omita nenhuma entidade.
    
    Categorias de entidades a extrair:
    1. PERSON: Santos, Papas (ex: Leão XIII, Pio X), bispos, padres, freiras, teólogos, destinatários de cartas, correspondentes, figuras históricas, bíblicas ou espirituais citadas.
    2. LOCATION: Cidades, países, capelas, santuários, mosteiros, dioceses, locais de retiro ou viagem (ex: Saint-Quentin, Roma, Val-de-Bois, Loreto, etc.).
    3. DATE: Datas específicas, anos, séculos ou festas litúrgicas citadas (ex: Festa do Sagrado Coração, Corpus Christi).
    4. ORGANIZATION: Congregações religiosas, ordens, periódicos/revistas (ex: Le Règne du Sacré-Cœur), jornais, institutos, colégios ou comitês da época.
    5. THEOLOGICAL_CONCEPT: Conceitos espirituais e teológicos fundamentais (ex: oblação, reparação, Sagrado Coração, reinado social, adoração eucarística, amor reparador, apostolado, ascese, etc.).
    6. DOCUMENT: Títulos de encíclicas (ex: Rerum Novarum, Annum Sacrum), livros, constituições religiosas, diretórios espirituais ou regulamentos.

    Além disso, analise o sentimento geral deste fragmento:
    - Um score de sentimento entre -1.0 (de aflição profunda, sofrimento espiritual, preocupação ou negatividade) e 1.0 (de alegria litúrgica, êxtase espiritual, esperança ou positividade).
    - Uma classificação ("POSITIVE", "NEGATIVE", "NEUTRAL").

    Retorne APENAS um objeto JSON válido, sem qualquer bloco de código markdown (como ```json) ou introdução, seguindo estritamente esta estrutura:
    {{
      "entities": [
        {{
          "name": "nome completo e exato da entidade encontrada",
          "type": "PERSON" ou "LOCATION" ou "DATE" ou "ORGANIZATION" ou "THEOLOGICAL_CONCEPT" ou "DOCUMENT",
          "explanation": "breve contexto em português de como esta entidade se relaciona com o texto analisado"
        }}
      ],
      "sentiment": {{
        "score": 0.0,
        "label": "POSITIVE" ou "NEGATIVE" ou "NEUTRAL"
      }}
    }}

    Texto para analisar:
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
        print(f"[GEMINI NLU] Aviso: falha ao extrair com modo JSON estrito: {e}. Tentando fallback sem formato estrito...", flush=True)
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
                
            data = json.loads(raw_text.strip())
            return data
        except Exception as fallback_err:
            print(f"[GEMINI NLU] Erro crítico no fallback da extração: {fallback_err}", flush=True)
            return {"entities": [], "sentiment": {"score": 0.0, "label": "NEUTRAL"}}
