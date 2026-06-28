# Progresso Atual (Atualizado)

## 1. Processamento de Ficheiros (Completo)
- Os ficheiros fonte soltos de *Dehondocs* e *Studia Dehoniana* foram processados, as capas indesejadas foram limpas e os ficheiros foram unidos por categoria/idioma.
- Resultado: A pasta de exportação `Obras_Dehon_Oracle` (no Desktop) contém agora apenas os PDFs Mestres altamente otimizados para ingestão de IA.

## 2. Infraestrutura na Nuvem (Completa)
- Identificado o estrangulamento nos buckets originais da OCI (Oracle Cloud).
- Criado um bucket novo e otimizado (`dehon-pdfs-limpos`).
- Desenvolvido e executado um script de eliminação Python (OCI SDK) que eliminou com sucesso **9.019** ficheiros lixo do bucket `dehon-cartas-e-corpus` e **15** ficheiros do `dehon-ia-documentos`.

## 3. Observabilidade e Testes (Completo)
- Integração profunda do Langfuse SDK no `main.py` usando `trace` e `span` para capturar a intenção, as citações da OCI, e interligar com o endpoint `/api/feedback` e o Supabase.
- Instalação e configuração do pacote oficial `langfuse` no `venv`.
- Desenvolvido e executado o script `scripts/importar_datasets.py` que inseriu com sucesso o **Dataset "dehon-rag-gold-standard"** na Cloud, contendo as "Perguntas de Ouro" transversais a temas históricos, teológicos, carismáticos, etc.
