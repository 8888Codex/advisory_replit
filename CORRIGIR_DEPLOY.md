# 🔧 Correção do Deploy - Erro 401

## ❌ PROBLEMAS IDENTIFICADOS

### Problema 1: Python backend não estava rodando
**Sintomas:**
- Erro 401 em `/api/auth/login` e `/api/auth/me`
- Console mostra "Failed to load resource: 401 Unauthorized"

**Causa:**
O Dockerfile original só iniciava o servidor Node, que tentava se conectar ao Python backend inexistente.

### Problema 2: Conflito de inicialização do Python
**Causa:**
O `server/index.ts` estava tentando iniciar o Python backend automaticamente mesmo em produção, causando conflito com o `start.sh`.

### Problema 3: Porta incorreta do servidor Node
**Causa:**
O servidor Node estava usando `PORT || '5000'` mas o deploy espera porta 3001. O `start.sh` não estava definindo `PORT=3001`.

### Problema 4: curl pode não estar disponível
**Causa:**
O `start.sh` usava `curl` para health check, mas pode não estar instalado no container.

---

## ✅ SOLUÇÃO APLICADA

### Arquivos Corrigidos:

1. ✅ **`start.sh`** 
   - Define `PORT=3001` explicitamente
   - Health check com fallback (curl → python → wget → timeout)
   - Inicia Python backend antes do Node

2. ✅ **`server/index.ts`**
   - **NÃO inicia Python em produção** (apenas em desenvolvimento)
   - Em produção, assume que `start.sh` já iniciou o Python

3. ✅ **`server/routes.ts`**
   - Adicionado endpoint `/api/health` que verifica Node e Python

4. ✅ **`Dockerfile`**
   - Garante instalação de `curl` e `wget` para health checks

---

## 🚀 COMO APLICAR A CORREÇÃO

### Opção A: Rebuild Completo (RECOMENDADO)

1. **Commit e push das correções:**

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit

# Adicionar arquivos corrigidos
git add Dockerfile start.sh server/index.ts server/routes.ts CORRIGIR_DEPLOY.md

# Commitar
git commit -m "fix: Corrigir deploy - evitar conflito Python, definir PORT=3001, adicionar health check Node"

# Push (você precisa fazer manualmente com suas credenciais)
git push origin main
```

2. **No Dokploy:**
   - Vá para a aplicação deployada
   - Clique em **"Rebuild"** ou **"Redeploy"**
   - Aguarde o build completo (~10-15 minutos)

### Opção B: Rebuild Via Interface (Mais Fácil)

1. **Acesse seu projeto no Dokploy**
   - URL: http://72.60.244.72:3000/dashboard/projects

2. **Selecione a aplicação**

3. **Faça as mudanças pelos arquivos:**
   - Na aba "Files" ou via terminal do container
   - Copie o conteúdo de `start.sh` e crie o arquivo
   - Atualize o `Dockerfile`

4. **Rebuild:**
   - Clique no botão "Rebuild"
   - Aguarde conclusão

---

## 📋 VERIFICAÇÃO PÓS-DEPLOY

### 1. Verificar Logs do Container

No Dokploy, veja os logs e procure por:

```
🚀 Iniciando O Conselho Marketing Advisory Platform
==================================================
✅ Todas as variáveis obrigatórias configuradas
✅ Diretórios criados
✅ Dependências Python OK
🐍 Iniciando Python backend (porta 5002)...
⏳ Aguardando Python backend inicializar...
✅ Python backend pronto! (PID: XXXX)
🟢 Iniciando Node server (porta 3001)...
==================================================
serving on port 3001
```

**IMPORTANTE:** Você NÃO deve ver a mensagem "Starting Python backend on port 5002..." do servidor Node em produção. Se aparecer, significa que o Node está tentando iniciar o Python (erro corrigido).

### 2. Testar Health Checks

```bash
# Backend Python
curl http://SUA-URL:5002/api/health

# Deve retornar: {"status": "healthy"}
```

```bash
# Frontend Node
curl http://SUA-URL:3001/api/health

# Deve retornar:
# {
#   "status": "ok",
#   "node": "healthy",
#   "python": "healthy",
#   "timestamp": "2024-..."
# }
```

### 3. Testar Login

- Acesse `http://SUA-URL:3001`
- O erro 401 deve ter desaparecido
- Console do navegador (F12) deve estar limpo

---

## 🆘 SE AINDA NÃO FUNCIONAR

### Problema: Python ainda não inicia

**Verificar:**
1. Python3 está instalado no container?
   ```bash
   docker exec -it advisory-app python3 --version
   ```

2. Dependências Python estão instaladas?
   ```bash
   docker exec -it advisory-app pip list | grep uvicorn
   ```

3. Caminho do python_backend está correto?
   ```bash
   docker exec -it advisory-app ls -la python_backend/
   ```

### Problema: Variáveis de ambiente

**Verificar no Dokploy** (aba Environment):
- ✅ `DATABASE_URL` configurado
- ✅ `ANTHROPIC_API_KEY` configurado
- ✅ `SESSION_SECRET` configurado

---

## 📊 CHECKLIST FINAL

Após rebuild, confirme:

- [ ] Logs mostram Python e Node iniciando
- [ ] Health check do Python responde (porta 5002)
- [ ] Health check do Node responde (porta 3001)
- [ ] Login funciona sem erro 401
- [ ] Console do navegador sem erros

---

## 🎯 PRÓXIMOS PASSOS APÓS LOGIN FUNCIONAR

1. **Criar usuário inicial** (se necessário):
   - Use o SQL em `criar_usuario_producao.sql`
   - Ou registre pela interface

2. **Testar funcionalidades:**
   - Criar/ativar persona
   - Chat com expert
   - Council analysis

3. **Configurar domínio** (opcional):
   - No Dokploy, aba "Domains"
   - Adicionar seu domínio customizado

---

**Tempo estimado para correção: 15-20 minutos** (incluindo rebuild)

