# 🔧 Correção do Deploy - Erro 401

## ❌ PROBLEMA IDENTIFICADO

O **Python backend não está rodando** no container Docker!

**Sintomas:**
- Erro 401 em `/api/auth/login` e `/api/auth/me`
- Console mostra "Failed to load resource: 401 Unauthorized"

**Causa:**
O Dockerfile original só iniciava o servidor Node, que tentava se conectar ao Python backend inexistente.

---

## ✅ SOLUÇÃO APLICADA

### Arquivos Corrigidos:

1. ✅ **`start.sh`** - Script que inicia AMBOS servidores (Node + Python)
2. ✅ **`Dockerfile`** - Atualizado para usar o `start.sh`

---

## 🚀 COMO APLICAR A CORREÇÃO

### Opção A: Rebuild Completo (RECOMENDADO)

1. **Commit e push das correções:**

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit

# Adicionar arquivos corrigidos
git add Dockerfile start.sh CORRIGIR_DEPLOY.md

# Commitar
git commit -m "fix: Adicionar start.sh para iniciar Python e Node corretamente"

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
✅ Variáveis de ambiente validadas
✅ Diretórios criados
🐍 Iniciando Python backend (porta 5002)...
⏳ Aguardando Python backend inicializar...
✅ Python backend pronto!
🟢 Iniciando Node server (porta 3001)...
```

### 2. Testar Health Checks

```bash
# Backend Python
curl http://SUA-URL:5002/api/health

# Deve retornar: {"status": "healthy"}
```

```bash
# Frontend Node
curl http://SUA-URL:3001/api/health

# Deve retornar algo como: {"status": "ok"}
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

