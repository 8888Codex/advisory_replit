# 🚀 Deploy no Netlify - Guia Completo

## ⚠️ IMPORTANTE: Arquitetura do Projeto

Este projeto tem **2 backends**:

1. **Backend Node.js** (Express) - `server/index.ts`
   - Gerencia autenticação, sessões, rotas
   - Funciona como proxy para o backend Python
   - ✅ **Pode rodar no Netlify Functions**

2. **Backend Python** (FastAPI) - `python_backend/main.py`
   - 18 especialistas em marketing (IA)
   - Sistema de enriquecimento de personas
   - Geração de análises com Claude
   - ❌ **NÃO pode rodar no Netlify** (Python não suportado)

---

## 🎯 OPÇÕES DE DEPLOY:

### **Opção 1: Frontend + Node no Netlify, Python Separado (RECOMENDADO)**

**Netlify:** Frontend React + Backend Node.js (como Functions)  
**Render/Railway:** Backend Python FastAPI

**Vantagens:**
- ✅ Frontend ultra-rápido no CDN do Netlify
- ✅ Node Functions gratuitas (125k requests/mês)
- ✅ Python backend em servidor dedicado
- ✅ Melhor performance para background tasks

**Configuração:**
1. Deploy frontend + Node no Netlify
2. Deploy Python no Render (gratuito)
3. Configurar variável `PYTHON_BACKEND_URL` no Netlify

---

### **Opção 2: Tudo no Vercel (MAIS SIMPLES)**

O Vercel suporta **Python** + **Node** + **React** no mesmo projeto!

**Vantagens:**
- ✅ Deploy unificado (1 comando)
- ✅ Suporte nativo para Python
- ✅ Serverless Functions automáticas
- ✅ Preview deployments
- ✅ Edge Network global

---

### **Opção 3: Tudo no Render**

Backend Python + Backend Node + Frontend estático

**Vantagens:**
- ✅ Suporte completo para Python
- ✅ Banco de dados PostgreSQL incluído
- ✅ Deploy direto do Github

---

## 💡 RECOMENDAÇÃO:

**Use Vercel!** É a melhor opção para este projeto porque:

1. ✅ Suporta Python nativo
2. ✅ Deploy automático do Github
3. ✅ Variáveis de ambiente fáceis
4. ✅ Logs em tempo real
5. ✅ Zero configuração extra

---

## 📦 PRÓXIMOS PASSOS (Vercel):

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Fazer login
vercel login

# 3. Deploy
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
vercel

# 4. Configurar variáveis de ambiente no dashboard
```

Variáveis necessárias:
- `DATABASE_URL` (Neon PostgreSQL)
- `ANTHROPIC_API_KEY`
- `YOUTUBE_API_KEY`
- `SESSION_SECRET`

---

## 🔄 ALTERNATIVA: Deploy Netlify (Frontend Only)

Se preferir Netlify para o frontend:

```bash
# 1. Login
netlify login

# 2. Inicializar
netlify init

# 3. Deploy
netlify deploy --prod
```

**Depois configure:**
- Backend Python no Render: https://render.com
- Variável `VITE_API_URL` no Netlify apontando para o Render

---

## ❓ Qual Opção Prefere?

1. **Vercel** (tudo junto, mais simples)
2. **Netlify + Render** (frontend no Netlify, backend separado)
3. **Render** (tudo junto, mais controle)

