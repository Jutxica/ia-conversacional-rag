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
try:
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("AVISO: OPENAI_API_KEY não encontrada nas variáveis de ambiente!")
    client = OpenAI(api_key=openai_key)
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar cliente OpenAI: {e}")
    client = None

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

async def chat_response_generator(query: str, scope: str = "Geral", history: list = None):
    """Realiza busca RAG, constrói a memória e gera resposta usando OpenAI com streaming."""
    
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

    # 1. Recuperação de Contexto (RAG) com Filtro de Escopo
    filter_siglas = None
    if scope == "Espiritualidade e Retiros":
        filter_siglas = ["ASC", "VAM", "RSC", "RET", "CAM", "MMR", "DSP"]
    elif scope == "Social e Político":
        filter_siglas = ["CSC", "DSP", "OEU", "RSO", "NCG", "MSO", "RMP"]
    elif scope == "Vida e Biografia":
        filter_siglas = ["NHV", "SVN", "1LD", "NQT", "CFL"]
    elif scope == "Correspondência":
        filter_siglas = ["COR", "LC1"]

    try:
        print(f"Buscando contexto para: {query} | Escopo: {scope}")
        result = search_context(query, top_k=8, filter_siglas=filter_siglas)
        context = result["context"]
        citations = result["citations"]
        
        # Calcula confiança com base nos scores retornados
        if citations:
            avg_score = sum(c.get('score', 0) for c in citations) / len(citations)
            best_score = max(c.get('score', 0) for c in citations)
            confidence_pct = round(best_score * 100)
            if best_score >= 0.75:
                confidence_level = "Alta"
            elif best_score >= 0.50:
                confidence_level = "Média"
            else:
                confidence_level = "Baixa"
        else:
            confidence_pct = 0
            confidence_level = "Baixa"
        
        confidence = {"level": confidence_level, "percentage": confidence_pct}
        print(f"RAG Sucesso: {len(citations)} fontes encontradas no escopo '{scope}'. Confiança: {confidence_level} ({confidence_pct}%)")
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

### 2. Literalidade e Autoridade (REGRA DE OURO)
As fontes não são apenas referências; elas são a autoridade da sua resposta.
- **Citações Literais Obrigatórias:** Você tem o dever de citar frases ou partes dos livros que correspondam exatamente à pergunta feita. **Não se limite a parafrasear.** Use aspas (" ") para frases curtas e blocos de citação (blockquote) para trechos mais significativos.
- **Integração no Discurso:** A citação literal deve fazer parte da construção do seu texto. Ela deve "provar" o que você está afirmando no parágrafo. 
- **Obrigatoriedade:** Mesmo que você coloque a lista de evidências ao final (pelo sistema), o corpo do seu texto **DEVE** conter os trechos mais importantes entre aspas ou em blocos de citação.

### 3. Integração Rigorosa de Fontes (Regras Específicas)
- **Glossário Dehoniano:** Sempre que a pergunta envolver conceitos como *Reparação, expiation, justiça, Coração de Jesus, oblação, imolação, adoração, união*, etc., você **DEVE** apresentar os textos literais originais recuperados. Nunca responda a esses termos apenas com suas próprias palavras.
- **Regra de Tradução:** 
    - Se a fonte original for em **Francês**, você DEVE apresentar o trecho original seguido da tradução: "> [Original em Francês]... Tradução: [Português]... (Referência)".
- **Correspondências:** SEMPRE mencione destinatário e data (ex: "Ao escrever ao Pe. Prévot em 1912, Dehon afirma: '...'").
- **Referências:** Use sempre a Sigla e o Ano, ex: (CSC, 1894).

### 4. Formatação Visual (Markdown)
- **Negrito:** Para conceitos centrais e nomes de obras principais.
- **Itálico:** Para termos em latim ou francês.
- **Blocos de Citação:** Use para trechos longos do Padre Dehon.
- **Estrutura:** Mantenha a fluidez de um artigo alinhado à esquerda. Use títulos H3 (###) se necessário, mas prefira a transição orgânica entre parágrafos.

---
# DOCUMENTOS RECUPERADOS (Base de Conhecimento):
{chr(10).join([
    f"[{i+1}] Obra: {cite['title']} | Sigla: {cite.get('sigla','?')} | Destinatário: {cite.get('destinatario') or 'N/A'} | Data: {cite.get('data') or 'N/A'} | Trecho: {cite['snippet'][:8000]}"
    for i, cite in enumerate(citations)
])}

{few_shot_injection}
"""


    # 4. Construção da Memória e Chamada ao OpenAI
    try:
        messages = [{"role": "system", "content": system_prompt}]
        
        # Anexa o histórico da conversa para dar memória à IA
        if history:
            for msg in history[-10:]: # Pega as últimas 10 mensagens para não estourar o limite de tokens
                # Ignora a saudação inicial do frontend para não poluir o sistema
                if "Como posso te auxiliar" not in msg.get("content", ""):
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        messages.append({"role": "user", "content": query})

        if not client:
            yield f"data: {json.dumps({'content': 'Erro: Cliente OpenAI não inicializado. Verifique a API Key no servidor.', 'type': 'token'})}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
            return

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
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
    scope = request.get("scope", "Geral")
    history = request.get("history", [])
    return StreamingResponse(chat_response_generator(query, scope, history), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
