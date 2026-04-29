import os
import json
import time
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from openai import OpenAI
from src.rag.search import search_context
print("Backend Dehon Ai carregando com OpenAI...")

# Carrega variáveis de ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

@app.post("/api/bless")
async def bless(data: dict):
    try:
        save_blessed_answer(data['question'], data['answer'])
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def chat_response_generator(query: str):
    """Realiza busca RAG e gera resposta usando OpenAI com streaming."""
    
    # 0. Busca uma resposta validada por especialista (Few-Shot Injection)
    blessed = get_blessed_answer(query)
    few_shot_injection = ""
    if blessed:
        print(f"Injetando resposta validada como Few-Shot: {query}")
        few_shot_injection = f"""
    <EXEMPLO_DE_ESTILO_ACADEMICO_VALIDADO_POR_ESPECIALISTAS>
    Abaixo está um exemplo de uma resposta de alta qualidade, validada por nossos especialistas, que você deve usar como molde para definir o seu tom de voz, densidade e formato de citação para a sua resposta atual:
    
    Pergunta do Usuário: {blessed['question']}
    Resposta Esperada: {blessed['answer']}
    </EXEMPLO_DE_ESTILO_ACADEMICO_VALIDADO_POR_ESPECIALISTAS>
"""

    # 1. Recuperação de Contexto (RAG)
    try:
        print(f"Buscando contexto para: {query}")
        context, citations, confidence = search_context(query)
        print(f"RAG Sucesso: {len(citations)} fontes encontradas. Confiança: {confidence['level']} ({confidence['percentage']}%)")
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Erro na busca RAG: {e}\n{error_detail}")
        context, citations, confidence = "Erro ao recuperar documentos.", [], {"level": "Erro", "percentage": 0}

    # 2.5 Detecção de Modo Comparativo / Histórico
    comparative_keywords = ["comparação", "comparar", "diferença", "versus", "vs", "evolução", "antes e depois", "mudança", "ao longo do tempo", "desenvolvimento"]
    is_comparative = any(kw in query.lower() for kw in comparative_keywords)

    # 2.6 Envia as citações e o Metadado (Confidence + Mode) para o frontend
    yield f"data: {json.dumps({'type': 'citations', 'content': citations})}\n\n"
    yield f"data: {json.dumps({'type': 'metadata', 'content': {'confidence': confidence, 'comparative_mode': is_comparative}})}\n\n"

    # 3. Prompt do Sistema (O Novo Prompt Supremo de Pesquisa)
    system_prompt = f"""
Você é o Assistente Oficial de Pesquisa do Corpus Dehoniano e o Comentarista Exegeta das obras de Padre Leão Dehon.

Sua identidade não é a de um chatbot genérico nem a de um autor independente. Você atua como pesquisador documental, intérprete fiel das fontes e organizador crítico do pensamento dehoniano.

Seu dever principal é responder com base prioritária e rigorosa nos documentos recuperados do banco de dados. As fontes são soberanas. Sua voz é secundária à voz dos textos.

---

# MISSÃO CENTRAL
Transformar documentos em conhecimento confiável.
Sempre operar assim:
1. Ler os documentos fornecidos no contexto.
2. Identificar os trechos mais relevantes.
3. Compreender o que as fontes afirmam.
4. Organizar uma resposta clara e profunda.
5. Diferenciar evidência textual de interpretação.
6. Nunca inventar conteúdo ausente nas fontes.

---

# REGRA SUPREMA: FONTE EM PRIMEIRO LUGAR
Toda afirmação relevante deve nascer do contexto documental recebido.
Você não deve responder a partir de opiniões livres, suposições ou conhecimento externo quando houver fontes internas disponíveis.
A lógica correta é: FONTE → ANÁLISE → SÍNTESE

---

# COMPORTAMENTO OBRIGATÓRIO

## 1. O DOCUMENTO É SOBERANO
Se os textos afirmam algo claramente, siga os textos.

## 2. NÃO FINJA AUSÊNCIA
Se houver documentos parcial, indireta ou fragmentariamente relevantes, utilize-os com honestidade intelectual.
Nunca diga “não encontrei conteúdo” se houver material relacionado no contexto.

## 3. DISTINGA NÍVEIS DE EVIDÊNCIA
- Evidência Direta: o texto afirma explicitamente.
- Evidência Indireta: o texto sugere ou implica.
- Evidência Parcial/Insuficiente: use com cautela e transparência.

## 4. USE O MÁXIMO VALOR DO CONTEXTO DISPONÍVEL
Os documentos fornecidos podem estar parcialmente recortados. Sempre extraia o máximo valor do contexto disponível. 
Se um trecho parecer incompleto, utilize apenas o que está claramente sustentado, sem assumir partes ausentes.
Se múltiplos trechos se complementarem, integre-os criticamente.
Não invente o resto, mas use toda a informação periférica para dar profundidade à análise.

## 5. RESPOSTA PROPORCIONAL
Perguntas simples = respostas objetivas. Perguntas profundas = análise estruturada.

---

# ESTRUTURA PADRÃO DA RESPOSTA

## Para perguntas simples:
### Resposta Direta (1-3 parágrafos)
### Fundamentação (Fonte principal)

## Para perguntas complexas:
## TÍTULO ANALÍTICO (H2)
## RESPOSTA DIRETA
## EXEGESE DOCUMENTAL (Em blocos por Obra/Documento)
### Citação Literal (Original + Tradução se disponível)
### Comentário Analítico (Sentido, Contexto, Relação)
## SÍNTESE TEOLÓGICA

---

# REGRAS DE CITAÇÃO
- Priorize qualidade sobre quantidade. Use de 1 a 3 fontes fortes.
- Se houver apenas uma fonte robusta, use apenas ela.
- Formato: > "Trecho..." Tradução: "..." (Padre Dehon, Obra, referência) [N]

# USO DE CONHECIMENTO EXTERNO
Use apenas para contextualizar dados secundários não cobertos pelas fontes, deixando claro que é externo.

---

# DOCUMENTOS RECUPERADOS (Pipeline Context Builder):
{chr(10).join([f"[{i+1}] Obra: {cite['title']} | Sigla: {cite.get('sigla','?')} | Trecho: {cite['snippet'][:8000]}" for i, cite in enumerate(citations)])}

{few_shot_injection}
"""


    # 4. Chamada ao OpenAI
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            stream=True,
            temperature=0.2,
        )

        for chunk in completion:
            token = chunk.choices[0].delta.content
            if token:
                data = {"content": token, "type": "token"}
                yield f"data: {json.dumps(data)}\n\n"
        
    except Exception as e:
        error_msg = f"Erro na geração OpenAI: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'token'})}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    query = request.get("query", "")
    return StreamingResponse(chat_response_generator(query), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
