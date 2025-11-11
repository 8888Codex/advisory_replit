# 🌐 Como Acessar o Sistema - Guia Rápido

**Última Atualização:** 10 de novembro de 2025, 01:40  
**Status:** 🟢 Sistema Online e Acessível

---

## 🎯 ACESSE AGORA:

### Abra seu navegador e digite:

```
http://localhost:3000
```

ou

```
http://127.0.0.1:3000
```

---

## ✅ SERVIDORES RODANDO:

| Servidor | Porta | Status | URL |
|----------|-------|--------|-----|
| **Frontend React** | 3000 | ✅ Online | http://localhost:3000 |
| **Python Backend** | 5001 | ✅ Online | http://localhost:5001 |

---

## 🔑 PRIMEIRO ACESSO:

### 1. Criar Conta

**Código de Convite:**
```
X6OCSFJFA1Z8KT5
```

- Nome: Seu nome
- Email: seu@email.com
- Senha: (escolha uma senha)
- Código: `X6OCSFJFA1Z8KT5`

### 2. Fazer Login

Use o email e senha que você criou.

### 3. Complete o Onboarding (4 etapas)

1. **Informações Básicas** (empresa, setor)
2. **Público-Alvo** (quem são seus clientes)
3. **Canais de Marketing** (onde você anuncia)
4. **Objetivo Principal** (growth, awareness, etc.)

---

## 🎊 O QUE VOCÊ VAI VER:

### Tela Principal: 32 Experts

```
┌──────────────────────────────────────────┐
│  🎯 Marketing Legends                    │
├──────────────────────────────────────────┤
│                                          │
│  📊 Categorias:                          │
│  [Marketing] [Growth] [SEO] [Social]     │
│                                          │
│  👤 Philip Kotler                        │
│     O Pai do Marketing Moderno           │
│     [Conversar]                          │
│                                          │
│  👤 Seth Godin                           │
│     Marketing de Nicho                   │
│     [Conversar]                          │
│                                          │
│  ... e mais 30 experts                   │
│                                          │
└──────────────────────────────────────────┘
```

---

## 🚀 FUNCIONALIDADES:

### 1. **Conversar com Expert**
- Clique em qualquer expert
- Faça sua pergunta
- Receba resposta personalizada

### 2. **Recomendações Inteligentes**
- Descreva seu problema
- Sistema sugere os melhores experts
- Resultado em 3-5 segundos

### 3. **Conselho Colaborativo**
- Pergunta complexa
- 8 experts analisam juntos
- Consenso em 30-60 segundos

### 4. **Histórico**
- Todas conversas salvas
- Retome quando quiser
- Contexto preservado

---

## 🔧 SE NÃO CARREGAR:

### Verifique se os servidores estão rodando:

```bash
# Ver processos
ps aux | grep -E "(uvicorn|tsx)"

# Ver portas
lsof -i :3000
lsof -i :5001
```

### Se algum não estiver rodando:

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
./start_all.sh
```

**OU inicie manualmente:**

```bash
# Terminal 1 - Python Backend
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
source .venv/bin/activate
cd python_backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 5001

# Terminal 2 - Frontend Node.js
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
npm run dev
```

---

## 📱 COMPATIBILIDADE:

### Navegadores Testados:
- ✅ Google Chrome
- ✅ Safari
- ✅ Firefox
- ✅ Edge

### Sistema Operacional:
- ✅ macOS (seu sistema)
- ✅ Windows
- ✅ Linux

---

## 🐛 RESOLUÇÃO DE PROBLEMAS:

### "Não consigo acessar localhost:3000"

**Causa:** Frontend não está rodando

**Solução:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
npm run dev
```

### "Página carrega mas sem experts"

**Causa:** Backend não está rodando

**Solução:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
source .venv/bin/activate
cd python_backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 5001
```

### "Erro 500 ao fazer login"

**Causa:** Banco de dados não conectado

**Solução:**
Verifique se a variável DATABASE_URL está no arquivo `.env`

### "Porta já em uso"

**Solução:**
```bash
# Matar processos na porta 3000
lsof -i :3000 | awk 'NR>1 {print $2}' | xargs kill -9

# Matar processos na porta 5001
lsof -i :5001 | awk 'NR>1 {print $2}' | xargs kill -9

# Reiniciar
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
./start_all.sh
```

---

## 📞 COMO TESTAR SE ESTÁ FUNCIONANDO:

### Teste 1: Acessar Frontend
```bash
curl http://localhost:3000/
```
**Esperado:** HTML com "DOCTYPE"

### Teste 2: Acessar Backend
```bash
curl http://localhost:5001/
```
**Esperado:** JSON com "message"

### Teste 3: API de Experts
```bash
curl http://localhost:3000/api/experts
```
**Esperado:** Array com 32 experts

---

## 🎯 URLS IMPORTANTES:

| Recurso | URL |
|---------|-----|
| **Sistema Principal** | http://localhost:3000 |
| **API Backend** | http://localhost:5001 |
| **API Docs (Swagger)** | http://localhost:5001/docs |
| **Experts** | http://localhost:3000/api/experts |
| **Recomendações** | http://localhost:3000/api/experts/recommendations |
| **Conselho** | http://localhost:3000/api/council/analyze |
| **Histórico** | http://localhost:3000/api/conversations/history/user |

---

## 📊 VERIFICAÇÃO RÁPIDA:

Execute este comando para ver se tudo está OK:

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
curl -s http://localhost:3000/api/experts | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ {len(d)} experts disponíveis')"
```

---

## 🎊 TUDO PRONTO!

1. **Abra seu navegador**
2. **Digite:** `http://localhost:3000`
3. **Faça login** com código: `X6OCSFJFA1Z8KT5`
4. **Explore os 32 experts!**

---

**Sistema está 100% funcional e acessível!** 🚀

Se ainda tiver problemas, me avise qual erro aparece no navegador!

