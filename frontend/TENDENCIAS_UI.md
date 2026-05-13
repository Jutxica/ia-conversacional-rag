# Tendências Modernas de UI (2024-2025)

Este documento centraliza as referências e os padrões estéticos que norteiam as escolhas de interface para o frontend da aplicação Dehon AI, fortemente inspirados pelo ecossistema React, TailwindCSS e o uso do paradigma implementado em bibliotecas como **shadcn/ui**.

## 1. Agentic UI & Generative Interfaces
Com o crescimento das IAs Autônomas, a UI não deve ser apenas reativa; ela precisa transparecer o pensamento do agente ("Thinking Indicator").
- **Estados Vazios e Skeletons:** Deixam de ser barras cinzas e passam a ter brilhos (*shimmer effects*) sutis ou mensagens contextuais.
- **Micro-metadados Dinâmicos:** Aparição suave de elementos como "Badges de Confiança" apenas quando há relevância matemática (a partir do momento que o RAG entrega uma pontuação).

## 2. Sombras Suaves, Bordas Finas e Efeitos "Glassmorphism"
O visual chapado puro é aprimorado por um "Flat 2.0".
- Uso massivo de bordas de 1px com cores extremamente sutis (`var(--border-subtle)`).
- Sombras empilhadas, simulando profundidade e fontes de luz mais naturais (`box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)`).
- Painéis e "Cards" flutuam levemente ao receber `hover` ou ganham anéis de foco (`ring-glow`) para evidenciar a navegabilidade.

## 3. Micro-Interações e Transições Orgânicas
Em vez de saltos abruptos, as interações ganham leveza e percepção de peso físico.
- Uso de `transition-timing-function` com curvas cúbicas mais complexas (ex: `cubic-bezier(0.4, 0, 0.2, 1)`).
- Efeitos magnéticos em botões chaves.
- Pequenos saltos (Scale) ao clicar em botões (ativo: `transform: scale(0.97)`).

## 4. Tipografia Otimizada (Hierarquia Visual e Acessibilidade)
Tamanhos modulares onde o espaçamento conta a estória da leitura.
- Letras sem serifa geométricas e neutras como *Inter* ou *Geist* para dados de interface.
- Letras serifadas clássicas, como *Lora*, para artigos extensos ou documentações humanizadas.
- O contraste adaptativo no "Dark Mode" para não cegar o usuário: trocar brancos puros por tons de gelo/pedra.

---
*Referência:* Implementação adaptada para CSS puro baseada na metodologia do Shadcn Studio e discussões abertas sobre *Frontend Tooling & Trends 2025*.
