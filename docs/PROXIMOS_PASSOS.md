# Próximos Passos (Next Steps)

Para fechar o ciclo de implementação atual, as seguintes ações dependem de interação manual na interface web:

## A. Oracle Cloud Infrastructure (OCI)
1. **Upload:** Entrar na Consola Web da Oracle, navegar até *Storage > Buckets > `dehon-pdfs-limpos`*. Fazer o upload manual (Drag & Drop) dos ficheiros PDF compilados que se encontram na pasta local `Obras_Dehon_Oracle`.
2. **Atualizar Agente:** Ir a *Analytics & AI > Generative AI Agents > Knowledge Bases*. Modificar as configurações da Base de Conhecimento para apontar (ou fazer link) para o novo bucket `dehon-pdfs-limpos`.
3. **Ingestão:** Clicar no botão **Ingest** ou **Sync** para que a IA consuma os novos PDFs processados.

## B. Langfuse (Observabilidade)
1. **Configurar Juiz LLM:** No painel web do Langfuse, aceder a *Settings > Models*. Adicionar a `OPENAI_API_KEY` para que o Langfuse possa invocar o GPT de forma autónoma.
2. **Ativar Avaliação de Alucinação:** Aceder à tab **Avaliadores (Evaluators)** no Langfuse. Criar um novo Avaliador com o *Prompt Teológico dehoniano* (ver documentação de DETALHES). Mapear `{{input}}` e `{{output}}`.
3. **Correr Teste de Regressão (Experiment):** Ir aos *Datasets*, abrir o `dehon-rag-gold-standard` que foi criado via script, e correr uma Experiência. Isto fará com que o Langfuse teste todas as perguntas de nível difícil contra o Agente atualizado da Oracle, gerando uma folha de excel/report com as classificações para garantir que o Agente não perdeu qualidade com os novos PDFs.
