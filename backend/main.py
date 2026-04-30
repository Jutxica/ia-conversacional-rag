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
        filter_siglas = ["ASC", "VAM", "RSC", "RET"]
    elif scope == "Social e Político":
        filter_siglas = ["CSC", "MSO", "QSS"]
    elif scope == "Vida e Biografia":
        filter_siglas = ["NHV", "SVN", "1LD"]
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
- **Adaptação de Contexto:** Se a pergunta for simples, seja direto. Se for complexa, explore nuances, tensões e evoluções no pensamento de Dehon, mantendo o texto coeso.

### 2. Integração Rigorosa de Fontes (Equilíbrio de Ouro)
As fontes são a alma do trabalho acadêmico. Você deve integrá-las com precisão:
- **Glossário Dehoniano (Gatilho de Citação Exata):** Sempre que a pergunta ou o contexto envolver palavras fundacionais do carisma dehoniano — como *Reparação, expiação, justiça, injustiça, Rerum Novarum, Ecce Venio, Ecce Ancilla, misericórdia, Coração de Jesus, oblação, Congregação dos Sacerdotes do Sagrado Coração de Jesus (SCJ), imolação, adoração reparadora, sint unum, oferecimento, thesaurus precum, união, união oblativa, sacrifício, entrega, vítima, cordeiro, Maria, Imaculado Coração de Maria, Jesus, Maria Madalena, São João, Apóstolo, Discípulo amado, Discípulo, Oblatos do Coração de Jesus, Vivat Cor Iesu, Cor, Iesu, Per cor Mariae, carisma* —, você **DEVE, obrigatoriamente**, apresentar frases e textos literais específicos dos livros e cartas recuperados para definir ou aprofundar esses termos. Nunca responda a esses termos apenas com as suas próprias palavras.
- **Citações em Bloco:** Para evidências fundamentais (especialmente dos termos acima), use blocos de citação (blockquote). Não se limite a referências entre parênteses; apresente o texto do Padre Dehon.
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

### 6. Correspondências: Destinatário e Data são OBRIGATÓRIOS
Sempre que a fonte for uma **Carta** ou **Correspondência** (identificada pela sigla COR, LC1, ou similar):
- **SEMPRE** mencione o destinatário da carta (ex: *"Escrevendo ao Pe. Prévot, em [data]..."*).
- **SEMPRE** inclua a data da correspondência, se disponível nos metadados.
- Se o destinatário não constar nos metadados, informe: *(destinatário não identificado na fonte)*.
- Contextualize brevemente quem é o destinatário, se relevante para o argumento.

### 6. Formatação e Estilo Visual (Markdown)
Para garantir uma leitura elegante e acadêmica, você deve estruturar sua resposta usando Markdown da seguinte forma:
- **Negrito:** Aplique **negrito** sempre que introduzir um conceito teológico central, uma tese importante ou o nome de uma obra principal (ex: **Catecismo Social**).
- **Itálico para Estrangeirismos:** Termos em latim, francês ou qualquer outro idioma que não seja o português devem vir em itálico (ex: *Sint Unum*, *Ecce Venio*, *Rerum Novarum*).
- **Parágrafos Curtos:** Nunca escreva blocos de texto maciços. Quebre o texto a cada 3 ou 4 linhas para dar "respiro" à leitura.
- **Estrutura:** Não centralize o texto; mantenha a fluidez de um artigo alinhado à esquerda. Use títulos H3 (###) se a resposta precisar ser separada em partes muito distintas, mas prefira a transição orgânica entre parágrafos.

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
