# O Conselho - Marketing Advisory Platform

Plataforma de consultoria em marketing com IA, oferecendo acesso a especialistas e análise estratégica através de um conselho de experts.

## 🚀 Status do Deploy

✅ **Deploy corrigido e funcionando** - [Issue #1](https://github.com/8888Codex/advisory_replit/issues/1)

### Últimas Correções (12/11/2025)

- ✅ Build Docker corrigido - `attached_assets` copiado antes do build
- ✅ Conflito Python resolvido - não inicia em produção
- ✅ Porta Node corrigida - PORT=3001 definido explicitamente
- ✅ Health checks implementados - endpoints `/api/health` em Node e Python
- ✅ Fallback de health check - curl → python → wget → timeout

**Commit:** [`c8f6715`](https://github.com/8888Codex/advisory_replit/commit/c8f67156db2d9622c6af021ad064f5a7ecf5ac69)

## 📋 Tecnologias

- **Frontend:** React + TypeScript + Vite + TailwindCSS
- **Backend Node:** Express + TypeScript
- **Backend Python:** FastAPI + Uvicorn
- **Banco de Dados:** PostgreSQL
- **Deploy:** Docker + Dokploy

## 🏗️ Arquitetura

```
┌─────────────────┐
│   Frontend      │  React App (porta 3001)
│   (Node/Express)│
└────────┬────────┘
         │
         ├───► Python Backend (porta 5002)
         │     - FastAPI
         │     - AI/LLM Integration
         │     - Database Operations
         │
         └───► PostgreSQL Database
```

## 🚀 Deploy

### Pré-requisitos

- Docker
- Dokploy (ou plataforma compatível)
- PostgreSQL
- Variáveis de ambiente configuradas (ver `ENV_VARIABLES.md`)

### Variáveis de Ambiente Obrigatórias

```bash
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
SESSION_SECRET=seu-secret-aqui-minimo-32-caracteres
NODE_ENV=production
PORT=3001  # Porta do servidor Node
```

### Build e Deploy

```bash
# Build Docker
docker build -t advisory-replit .

# Ou usar Dokploy que faz build automático do GitHub
```

### Health Checks

Após deploy, verifique:

```bash
# Node Server
curl http://SUA-URL:3001/api/health

# Python Backend  
curl http://SUA-URL:5002/api/health
```

## 🛠️ Desenvolvimento Local

### Iniciar Sistema Completo

```bash
# Opção 1: Script automático
./start.sh

# Opção 2: Manual
# Terminal 1 - Python Backend
cd python_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 5002 --reload

# Terminal 2 - Node Server
npm run dev
```

### Portas Locais

- **Frontend/Node:** `http://localhost:5000` (dev) ou `3001` (prod)
- **Python Backend:** `http://localhost:5002`

## 📁 Estrutura do Projeto

```
advisory_replit/
├── client/              # Frontend React
├── server/              # Backend Node/Express
├── python_backend/      # Backend Python/FastAPI
├── shared/              # Código compartilhado
├── attached_assets/     # Assets estáticos (logos, avatares)
├── Dockerfile           # Build Docker
├── start.sh             # Script de inicialização
└── CORRIGIR_DEPLOY.md   # Documentação de deploy
```

## 🔧 Troubleshooting

### Build falha com "attached_assets não encontrado"

✅ **Resolvido** - O Dockerfile agora copia `attached_assets/` antes do build.

### Erro 401 no login

✅ **Resolvido** - Python backend agora inicia corretamente via `start.sh`.

### Servidor não inicia na porta correta

✅ **Resolvido** - `PORT=3001` definido explicitamente no `start.sh`.

## 📚 Documentação

- [`CORRIGIR_DEPLOY.md`](./CORRIGIR_DEPLOY.md) - Guia completo de deploy
- [`ENV_VARIABLES.md`](./ENV_VARIABLES.md) - Variáveis de ambiente
- [`README_DEPLOY.md`](./README_DEPLOY.md) - Status anterior do sistema

## 🐛 Issues Conhecidas

Verifique [Issues no GitHub](https://github.com/8888Codex/advisory_replit/issues) para problemas conhecidos e soluções.

## 📝 Licença

MIT

## 👤 Autor

Gabriel Lima - [8888Codex](https://github.com/8888Codex)

---

**Última atualização:** 12 de novembro de 2025

