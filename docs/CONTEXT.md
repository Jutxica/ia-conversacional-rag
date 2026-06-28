# Contexto do Projeto (Dehon AI)

## Origem e Propósito
O projeto nasceu da necessidade de unificar e tornar pesquisável todo o massivo acervo histórico do Padre Dehon (Coleções *Dehondocs* e *Studia Dehoniana*). O objetivo não é ser apenas um chatbot genérico, mas sim um assistente rigoroso, fundamentado e teológico.

## Desafios Ultrapassados e Decisões Arquiteturais
1. **Otimização do RAG (Retrieval):**
   - *Problema:* A Oracle OCI perde-se ou não dá peso suficiente a ficheiros quando o bucket tem milhares de pequenos ficheiros `.txt` ou `.pdf` carregados em massa.
   - *Solução:* Foi desenvolvida uma pipeline em Python (`pypdf`) que limpa, junta e agrupa centenas de ficheiros em PDFs "Mestres" organizados por idioma e categoria (ex: `Studia_Dehoniana_PT_COMPLETO.pdf`). Isto aumentou drasticamente a precisão da IA e forçou o modelo a respeitar o contexto global.

2. **Limitações de Interface da Oracle Cloud:**
   - *Problema:* A consola web da Oracle Cloud Infrastructure bloqueia eliminações em massa (mais de 1.000 ficheiros).
   - *Solução:* Criação de scripts locais através do SDK do Python para a Oracle que gerem via código as eliminações em bloco (`delete_object`), ultrapassando as limitações do Web UI.

3. **Garantia de Qualidade (Quality Assurance) - Langfuse:**
   - *Problema:* O feedback manual do utilizador (Polegar para Cima/Baixo) tem baixa taxa de adesão.
   - *Solução:* Substituição parcial da dependência humana por ferramentas de **LLM-as-a-Judge**. O Langfuse foi implementado no core do backend para capturar os inputs/outputs (Traces) e usar uma segunda inteligência (OpenAI) para atribuir Scores invisíveis, verificando proativamente casos de "Alucinação" ou "Falta de Relevância Teológica".
