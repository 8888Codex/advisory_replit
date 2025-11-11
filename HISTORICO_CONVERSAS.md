# 💬 Sistema de Histórico de Conversas

**Status:** ✅ Implementado (aguardando testes)  
**Data:** 10 de novembro de 2025

---

## 🎯 Funcionalidades Criadas:

### 1. **Armazenamento de Conversas** ✅
Todas as conversas são salvas no banco Neon PostgreSQL na tabela `conversations`:

```sql
conversations:
  - id (VARCHAR) - ID único da conversa
  - expertId (VARCHAR) - ID do expert
  - userId (VARCHAR) - ID do usuário (para filtrar)
  - title (TEXT) - Título da conversa
  - createdAt (TIMESTAMP) - Data de criação
  - updatedAt (TIMESTAMP) - Última atualização
```

### 2. **Armazenamento de Mensagens** ✅
Todas as mensagens são salvas na tabela `messages`:

```sql
messages:
  - id (VARCHAR) - ID único da mensagem
  - conversationId (VARCHAR) - ID da conversa
  - role (TEXT) - 'user' ou 'assistant'
  - content (TEXT) - Conteúdo da mensagem
  - createdAt (TIMESTAMP) - Data/hora
```

---

## 📡 APIs Criadas:

### 1. **GET /api/conversations**
Lista todas as conversas do usuário autenticado

**Query Parameters:**
- `expertId` (opcional) - Filtrar por expert específico

**Resposta:**
```json
[
  {
    "id": "uuid",
    "expertId": "seed-philip-kotler",
    "title": "Marketing Strategy",
    "createdAt": "2025-11-10T...",
    "updatedAt": "2025-11-10T..."
  }
]
```

### 2. **GET /api/conversations/history/user** ⭐ NOVO
Lista conversas com DETALHES completos (expert, preview, contagem)

**Query Parameters:**
- `limit` (opcional, default: 50) - Quantas conversas retornar

**Resposta:**
```json
[
  {
    "id": "uuid",
    "expertId": "seed-philip-kotler",
    "expertName": "Philip Kotler",
    "expertAvatar": "/avatars/philip-kotler.png",
    "expertCategory": "marketing",
    "title": "Marketing Strategy",
    "messageCount": 12,
    "lastMessage": "Ótima pergunta! Vou explicar...",
    "createdAt": "2025-11-10T...",
    "updatedAt": "2025-11-10T..."
  }
]
```

### 3. **GET /api/conversations/{id}**
Busca uma conversa específica

### 4. **GET /api/conversations/{id}/messages**
Busca TODAS as mensagens de uma conversa (para retomar)

**Resposta:**
```json
[
  {
    "id": "uuid",
    "conversationId": "conv-id",
    "role": "user",
    "content": "Como fazer marketing digital?",
    "createdAt": "2025-11-10T..."
  },
  {
    "id": "uuid",
    "conversationId": "conv-id",
    "role": "assistant",
    "content": "Ótima pergunta! Aqui está...",
    "createdAt": "2025-11-10T..."
  }
]
```

### 5. **POST /api/conversations**
Cria nova conversa (automaticamente associa ao userId da sessão)

**Body:**
```json
{
  "expertId": "seed-philip-kotler",
  "title": "Minha conversa sobre marketing"
}
```

---

## 💻 Como Usar no Frontend:

### 1. **Listar Histórico de Conversas**

```typescript
// Buscar histórico completo com detalhes
const response = await fetch('/api/conversations/history/user');
const conversations = await response.json();

// Cada conversa tem:
// - expertName, expertAvatar, expertCategory
// - messageCount (quantas mensagens)
// - lastMessage (preview)
// - updatedAt (ordenado por mais recente)
```

### 2. **Retomar Conversa**

```typescript
// 1. Usuário clica em uma conversa do histórico
const conversationId = "uuid-da-conversa";

// 2. Buscar todas as mensagens
const messages = await fetch(`/api/conversations/${conversationId}/messages`);
const history = await messages.json();

// 3. Exibir histórico no chat
history.forEach(msg => {
  if (msg.role === 'user') {
    // Mostrar mensagem do usuário
  } else {
    // Mostrar resposta do expert
  }
});

// 4. Usuário pode continuar conversando
// (envia nova mensagem para o mesmo conversationId)
```

### 3. **Continuar Conversa Existente**

```typescript
// Enviar nova mensagem em conversa existente
await fetch(`/api/conversations/${conversationId}/messages`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: "Mais uma pergunta..."
  })
});

// O sistema automaticamente:
// 1. Carrega TODO o histórico anterior
// 2. Passa para a IA (contexto preservado)
// 3. IA responde considerando tudo que foi dito antes
```

---

## 🎨 Sugestão de UI:

### Página de Histórico:

```
┌─────────────────────────────────────────────┐
│  📜 Histórico de Conversas                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ 👤 Philip Kotler                     │  │
│  │ 📝 Marketing Strategy                 │  │
│  │ 💬 12 mensagens                       │  │
│  │ 🕐 Atualizado: há 2 horas            │  │
│  │ "Ótima pergunta! Vou explicar..."   │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ 👤 Seth Godin                        │  │
│  │ 📝 Marketing Moderno                  │  │
│  │ 💬 8 mensagens                        │  │
│  │ 🕐 Atualizado: há 1 dia              │  │
│  │ "Marketing é sobre conexão..."       │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔧 Métodos Criados no Storage:

### `get_user_conversations(user_id, expert_id?)`
- Filtra conversas por usuário
- Opcionalmente filtra por expert
- Ordenado por updatedAt DESC (mais recentes primeiro)

### `create_conversation_with_user(data, user_id)`
- Cria conversa associada ao usuário
- Garante rastreamento correto

---

## 📊 Exemplos de Uso:

### Exemplo 1: Mostrar Últimas 10 Conversas

```python
GET /api/conversations/history/user?limit=10

# Retorna array com:
# - Nome e avatar do expert
# - Título da conversa
# - Quantas mensagens tem
# - Preview da última mensagem
# - Quando foi atualizada
```

### Exemplo 2: Filtrar Conversas com Philip Kotler

```python
GET /api/conversations?expertId=seed-philip-kotler

# Retorna apenas conversas com Philip Kotler
```

### Exemplo 3: Carregar Conversa Completa

```python
# 1. Buscar conversa
GET /api/conversations/{id}

# 2. Buscar mensagens
GET /api/conversations/{id}/messages

# Agora tem TODO o contexto para exibir e continuar
```

---

## ✨ Benefícios:

1. ✅ **Contexto Preservado** - IA lembra de TUDO que foi dito
2. ✅ **Múltiplas Conversas** - Pode ter várias com mesmo expert
3. ✅ **Organizado** - Fácil de encontrar conversas antigas
4. ✅ **Preview** - Vê última mensagem sem abrir
5. ✅ **Filtros** - Por expert, por data, etc.
6. ✅ **Performance** - Paginado (limit)

---

## 🎯 Como Implementar no Frontend:

### 1. Criar Página de Histórico (`/conversations` ou `/history`)

```tsx
// client/src/pages/ConversationHistory.tsx

import { useQuery } from '@tanstack/react-query';

export function ConversationHistory() {
  const { data: conversations } = useQuery({
    queryKey: ['/api/conversations/history/user'],
    queryFn: async () => {
      const res = await fetch('/api/conversations/history/user?limit=20');
      return res.json();
    }
  });

  return (
    <div>
      <h1>Minhas Conversas</h1>
      {conversations?.map(conv => (
        <ConversationCard
          key={conv.id}
          conversation={conv}
          onClick={() => navigate(`/chat/${conv.id}`)}
        />
      ))}
    </div>
  );
}
```

### 2. Página para Retomar Conversa

```tsx
// client/src/pages/ResumeConversation.tsx

export function ResumeConversation({ conversationId }) {
  // Buscar mensagens anteriores
  const { data: history } = useQuery({
    queryKey: [`/api/conversations/${conversationId}/messages`],
  });

  // Mostrar histórico + permitir novas mensagens
  return (
    <ChatInterface
      conversationId={conversationId}
      initialMessages={history}
      allowNewMessages={true}
    />
  );
}
```

---

## 📝 TODO (Para Implementar no Frontend):

- [ ] Criar página `/conversations` para listar histórico
- [ ] Componente `ConversationCard` para cada conversa
- [ ] Botão "Retomar" que abre a conversa
- [ ] Carregar mensagens antigas ao abrir
- [ ] Permitir continuar conversando
- [ ] Filtros (por expert, por data)
- [ ] Busca nas conversas
- [ ] Deletar conversas antigas

---

## 🧪 Testes Via API:

```bash
# Listar conversas do usuário
curl "http://localhost:3000/api/conversations"

# Ver histórico completo
curl "http://localhost:3000/api/conversations/history/user"

# Buscar mensagens de uma conversa
curl "http://localhost:3000/api/conversations/UUID/messages"

# Criar nova conversa
curl -X POST "http://localhost:3000/api/conversations" \
  -H "Content-Type: application/json" \
  -d '{"expertId":"seed-philip-kotler","title":"Minha conversa"}'
```

---

**Criado por:** IA Assistant  
**Feature:** Histórico de Conversas  
**Status:** Backend completo, falta implementar UI

🎯 **Próximo Passo:** Criar interface para visualizar e retomar conversas!

