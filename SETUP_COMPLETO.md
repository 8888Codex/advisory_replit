# ✅ Setup Completo - Advisory Replit

Data: 9 de novembro de 2025

## 📋 Status do Setup

### ✅ Tarefas Concluídas

1. **Variáveis de Ambiente**
   - ✅ Arquivo `.env` criado com todas as chaves de API
   - ✅ DATABASE_URL configurado (Neon PostgreSQL)
   - ✅ ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, YOUTUBE_API_KEY
   - ✅ GOOGLE_API_KEY, OPENAI_API_KEY, RESEND_API_KEY
   - ✅ SESSION_SECRET gerado automaticamente
   - ✅ NODE_ENV=development

2. **Dependências Node.js**
   - ✅ 631 pacotes instalados via `npm install`
   - ✅ React, Express, Drizzle ORM, Anthropic SDK
   - ✅ Radix UI, TailwindCSS, TanStack Query
   - ✅ Todas as dependências frontend e backend Node

3. **Dependências Python**
   - ✅ 175 pacotes instalados via `uv sync`
   - ✅ FastAPI, Uvicorn, AsyncPG
   - ✅ CrewAI e CrewAI Tools (framework multi-agente)
   - ✅ Anthropic, OpenAI, Google GenAI
   - ✅ ChromaDB, LanceDB (bancos vetoriais)
   - ✅ YouTube Transcript API, Perplexity integração

4. **Banco de Dados Neon**
   - ✅ Conexão PostgreSQL estabelecida
   - ✅ 27 tabelas criadas:
     - users, invite_codes, onboarding_status
     - password_reset_tokens, login_audit, audit_logs
     - feature_flags, api_costs, content_flags
     - experts, conversations, messages
     - business_profiles, personas, personas_deep, user_personas
     - council_sessions, council_participants, council_insights
     - council_messages, expert_collaboration_graph
     - user_profiles_extended, user_activity, user_favorites
     - user_preferences

5. **Python Backend (FastAPI)**
   - ✅ Servidor inicia corretamente na porta 5001
   - ✅ Health check respondendo: `{"message":"O Conselho Marketing Legends API","status":"running"}`
   - ✅ 18 experts seed carregados do CloneRegistry
   - ✅ Integração com PostgreSQL funcionando
   - ✅ CORS configurado para desenvolvimento

6. **Node.js Server + Frontend**
   - ✅ Servidor Express rodando na porta 5000
   - ✅ Proxy para Python backend configurado
   - ✅ Frontend React servido corretamente
   - ✅ Sistema de sessões configurado

## 🚀 Como Rodar o Projeto

### Opção 1: Iniciar Tudo de Uma Vez
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
./start_all.sh
```
Inicia Python backend (5001) e Node.js frontend (5000) simultaneamente.

### Opção 2: Iniciar Separadamente

**Python Backend:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
cd python_backend
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

**Node.js Frontend:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
npm run dev
```

## 🔧 Portas Utilizadas

- **5000** - Node.js Server + Frontend React
- **5001** - Python FastAPI Backend

## 📦 Estrutura do Projeto

```
advisory_replit/
├── .env                    # Variáveis de ambiente (criado)
├── .venv/                  # Virtual environment Python
├── node_modules/           # Dependências Node.js
├── client/                 # Frontend React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   └── public/
│       └── avatars/        # 18 avatares dos experts
├── server/                 # Backend Node.js (Express)
│   ├── index.ts           # Servidor principal
│   └── routes.ts          # Rotas API
├── python_backend/         # Backend Python (FastAPI)
│   ├── main.py            # API principal (✅ atualizado com load_dotenv)
│   ├── clones/            # 18 personalidades de marketing
│   │   ├── philip_kotler.py
│   │   ├── seth_godin.py
│   │   └── ...
│   └── tools/             # Ferramentas (Perplexity, YouTube, etc)
├── shared/
│   └── schema.ts          # Schema banco de dados
├── package.json
├── pyproject.toml
└── start_all.sh           # Script para iniciar tudo
```

## 🎭 Experts Disponíveis (18)

1. Philip Kotler - Marketing Strategy
2. Seth Godin - Marketing
3. David Ogilvy - Advertising
4. Gary Vaynerchuk - Social Media
5. Simon Sinek - Leadership
6. Neil Patel - SEO/Growth
7. Eugene Schwartz - Copywriting
8. Claude Hopkins - Direct Response
9. Jay Abraham - Marketing Strategy
10. Dan Kennedy - Direct Marketing
11. Robert Cialdini - Persuasion
12. Donald Miller - Storytelling
13. Ann Handley - Content Marketing
14. Al Ries - Positioning
15. David Aaker - Brand Strategy
16. Drayton Bird - Direct Marketing
17. Jay Levinson - Guerrilla Marketing
18. Daniel Kahneman - Behavioral Economics

## 🔐 Segurança

- ✅ Variáveis de ambiente não commitadas (.env no .gitignore)
- ✅ SESSION_SECRET único gerado
- ✅ Conexão PostgreSQL com SSL (sslmode=require)
- ✅ CORS configurado para desenvolvimento

## 📊 Banco de Dados

**Provider:** Neon PostgreSQL
**Status:** ✅ Conectado e operacional
**Tabelas:** 27 criadas e prontas
**Usuários:** 0 (banco novo, aguardando registro)

## 🎯 Próximos Passos para Desenvolvimento

1. ✅ Sistema configurado e pronto
2. 🔄 Criar primeiro usuário via interface
3. 🔄 Testar chat com experts
4. 🔄 Testar Council Room (múltiplos experts)
5. 🔄 Implementar novas funcionalidades
6. 🔄 Fazer deploy em produção (Replit/Vercel)

## 🐛 Troubleshooting

Se algum serviço não iniciar:

1. **Verificar variáveis de ambiente:**
   ```bash
   cat .env | grep -E "DATABASE_URL|ANTHROPIC"
   ```

2. **Limpar processos antigos:**
   ```bash
   pkill -f uvicorn
   pkill -f tsx
   ```

3. **Reinstalar dependências:**
   ```bash
   npm install
   uv sync
   ```

4. **Verificar conexão com banco:**
   ```bash
   python3 -c "import asyncpg, asyncio, os; from dotenv import load_dotenv; load_dotenv(); asyncio.run(asyncpg.connect(os.getenv('DATABASE_URL')))"
   ```

## ✨ Features Implementadas

- ✅ Sistema de autenticação com sessões
- ✅ 18 clones de experts com alta fidelidade
- ✅ Chat 1-on-1 com experts
- ✅ Council Room (múltiplos experts)
- ✅ Persona do usuário com enrichment
- ✅ Analytics e insights
- ✅ Integração com APIs externas (Perplexity, YouTube)
- ✅ Sistema multi-LLM (Claude, GPT, Gemini)
- ✅ Banco vetorial para memória

---

**Setup realizado com sucesso! 🎉**

O projeto está pronto para desenvolvimento e testes.

