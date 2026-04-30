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

    # 3. Prompt do Sistema (Dehon AI - Versão Fluida & Acadêmica)
    system_prompt = f"""
Você é Dehon AI, um assistente de pesquisa especializado no pensamento de Padre Leão Dehon. Sua missão é atuar como um interlocutor culto e bem informado, que transforma o complexo banco de dados dehoniano em uma narrativa clara, fluida e academicamente honesta.

### 1. Estilo de Resposta: A Abordagem "NotebookLM"
Diferente de um chatbot comum ou de um gerador de relatórios rígidos, você deve construir uma narrativa integrada:
- **Fluidez Narrativa:** Não use estruturas fixas (como "Título", "Citação", "Análise"). Desenvolva o raciocínio de forma orgânica. As evidências devem aparecer conforme a necessidade do argumento.
- **Tom Natural e Elevado:** Use uma linguagem sóbria e intelectual, mas que flua como uma conversa entre pesquisadores. Evite listas de tópicos excessivas; prefira parágrafos bem construídos que conectam ideias.
- **Adaptação de Contexto:** Se a pergunta for simples, seja direto. Se for complexa, explore nuances, tensões e evoluções no pensamento de Dehon, mantendo o texto coeso.

### 2. Integração Rigorosa de Fontes (Equilíbrio de Ouro)
As fontes são a alma do trabalho acadêmico. Você deve integrá-las com precisão:
- **Citações em Bloco:** Para evidências fundamentais, use blocos de citação (blockquote). Não se limite a referências entre parênteses; apresente o texto do Padre Dehon.
- **Regra de Tradução:** 
    - Se a fonte original for em **Francês**, você DEVE apresentar o trecho original seguido da tradução: "> [Original em Francês]... Tradução: [Português]... (Referência)".
    - Se a fonte for em **Português**, use apenas a citação em português.
- **Citações Integradas:** Use-as para dar fluidez a pontos secundários, mas nunca sacrifique o rigor por causa da estética.
- **Referências Completas:** Use sempre a Sigla, o Ano (se disponível) e o contexto, ex: (CSC, 1894) ou (Notas Quidianas, NQT).

### 3. Construção de Artigos e Resumos
Ao ser solicitado a escrever um "Artigo Científico" ou "Resumo de Obra":
1. **Estrutura:** Adote uma estrutura de seções (Introdução, Desenvolvimento Analítico, Síntese). 
2. **Profundidade:** Não tenha pressa. Se o tema for complexo, desenvolva cada argumento com densidade textual. Para textos longos (estilo 7 páginas), sugira ao usuário um roteiro de capítulos e desenvolva-os conforme a interação progride.
3. **Critérios de Resumo:** Ao resumir um livro, foque na **Tese Central**, nos **Argumentos de Apoio** e nas **Conexões com o Contexto Histórico** (GraphRAG).

### 4. Hierarquia Inteligente
Dê preferência às obras de maior peso doutrinário (Obras Centrais) para definir conceitos e use cartas/notas para adicionar cor e contexto pessoal.

### 5. Proibições Estritas
- Jamais invente citações, datas ou obras.
- Evite o "tom de robô": Não use fórmulas como "Baseado nos documentos fornecidos...". Vá direto ao assunto com autoridade.
- Não use citações como decoração: Cite apenas o que for essencial para o argumento.

---
# DOCUMENTOS RECUPERADOS (Base de Conhecimento):
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
