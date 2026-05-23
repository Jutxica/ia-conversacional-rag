# Plano de Melhorias — Painel Admin

## 1. Unificar as Duas Implementações

Existem **duas** versões do dashboard admin:

| `src/admin/AdminDashboardPage.tsx` | `src/components/admin/AdminDashboard.tsx` |
|---|---|
| Full-page com sidebar fixa | Modal/overlay |
| Auth via JWT (login user/senha) | Auth via Supabase session |
| Endpoints com `Authorization: Bearer <token>` | **Sem auth headers** → quebrado (403) |

### Ação
- Escolher **uma** abordagem (recomendo a full-page por ser mais escalável)
- Se optar pelo modal, arrumar os auth headers
- Se optar pela full-page, transportar as melhorias de UX do modal e remover o modal

## 2. Funcionalidades a Adicionar

### Logs de Busca
- Tabela com histórico de perguntas dos usuários
- Colunas: query, intent, confiança, número de citações, timestamp
- Filtro por data e por nível de confiança
- Endpoint já existe: `GET /api/feedback/gaps`

### Gestão de Siglario
- CRUD visual de siglas (já existe nos endpoints, falta UI)
- Tabela com: sigla, título, categoria, peso, url_code
- Modal de edição inline

### Gestão de Blessed Answers
- Lista de respostas validadas com busca
- CRUD completo (já existe nos endpoints)
- Indicador de uso (quantas vezes foi injetada como few-shot)

### Métricas do Sistema
- Total de chats realizados
- Feedback positivo vs negativo (taxa de acerto)
- Distribuição de intenções detectadas (HISTORICAL, THEOLOGICAL, CITATION, GENERAL)
- Top 5 gaps de conhecimento (consultas com baixa confiança)
- Gráficos simples (pode ser CSS puro ou biblioteca leve como recharts)

### Forçar Re-ingestão
- Botão "Re-processar" ao lado de cada documento
- Ação: DELETE + re-upload automático
- Feedback de progresso com etapas (extração → chunking → embedding → inserção)

### Visualização de Chunks
- Ao clicar num documento, mostrar lista de chunks gerados
- Ver conteúdo de cada chunk, metadados (sigla, peso, destinatário)
- Ajuda a depurar problemas de chunking

## 3. Melhorias de UX

### Splash Screen
- **Problema:** `AdminApp.tsx` força 1s de splash mesmo se auth resolver em 50ms
- **Solução:** Remover `setTimeout` e mostrar loading apenas enquanto a Promise do `getSession()` não resolveu

### Modal vs Página
- **Problema:** Admin como modal perde estado ao recarregar a página
- **Solução:** Usar React Router com rotas tipo `/admin/corpus`, `/admin/siglario`, `/admin/logs`

### Progresso Real no Upload
- **Problema:** Barra de progresso indeterminada (animação CSS infinita)
- **Solução:** Usar WebSocket ou polling do endpoint de status para progresso real (etapas: "Extraindo texto...", "Gerando chunks...", "Vetorizando...", "Inserindo no banco...")

### Confirmação de Exclusão
- **Problema:** `confirm()` nativo do browser — feio e não estilizado
- **Solução:** Modal de confirmação customizado com mensagem clara ("Isso removerá 47 chunks do corpus")

## 4. Arquitetura

### CSS
- **Problema:** Estilos do admin misturados no `src/index.css` (linhas 479–905) com os estilos do chat
- **Solução:** Mover tudo para `src/admin/admin.css` (já existe, mas está vazio — o conteúdo foi parar no index.css)

### Tipagem
- **Problema:** `DocItem` e outras interfaces duplicadas nos dois arquivos admin
- **Solução:**
  ```ts
  // src/admin/types.ts
  export interface DocItem {
    source_id: string
    title: string
    sigla: string
    document_weight: number | string
    chunks: number
  }
  ```

### Autenticação
- **Problema:** Dois sistemas (JWT e Supabase) para a mesma finalidade
- **Solução:** Decidir por **um**:
  - **JWT** → já implementado no backend, sem dependência externa
  - **Supabase** → se o resto do app já usa Supabase auth, unificar faz sentido
  - Não manter os dois

## 5. Proteções de Segurança

### Taxa de Upload
- Limitar uploads por minuto (evita abuso)

### Validação de Arquivo
- Verificar se é PDF verdadeiro (não só extensão)
- Limitar tamanho (já existe no frontend, mas não no backend)

### Auditoria
- Log de ações: quem fez upload/exclusão de qual documento e quando
- Tabela `admin_audit_log` no banco

## Resumo de Prioridades

```
P0 - Unificar implementações + arrumar auth headers
P0 - CSS do admin separado do index.css
P1 - Logs de busca (já tem endpoint)
P1 - Gestão de siglario com UI (já tem endpoint)
P1 - Remover splash forçada de 1s
P2 - Métricas do sistema com gráficos
P2 - Visualização de chunks
P2 - Barra de progresso real no upload
P3 - Auditoria de ações
P3 - Modal de confirmação customizado
```
