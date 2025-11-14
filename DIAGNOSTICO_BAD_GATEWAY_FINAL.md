# 🔍 Diagnóstico Final: Bad Gateway Persistente

## ❌ Problema

**Erro:** `Bad Gateway` mesmo após corrigir PORT=3001  
**Status:** Aplicação pode não estar iniciando ou não está acessível

---

## 🔍 DIAGNÓSTICO PASSO A PASSO (EXECUTE NA ORDEM)

### ✅ Passo 1: Verificar Logs COMPLETOS da Aplicação

**No Dokploy:**

1. Vá na aba **"Logs"**
2. **Role até o TOPO** (não apenas as últimas linhas)
3. Procure por logs **APÓS** o build (depois de "Docker Deployed: ✅")
4. **Copie TODOS os logs desde o início** e me envie

**O que procurar:**

#### ✅ SUCESSO - Deve aparecer:
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
serving on port 3001 (host: 0.0.0.0)
```

#### ❌ ERRO - Se aparecer:
```
❌ ERROR: DATABASE_URL não configurado
❌ ERROR: ANTHROPIC_API_KEY não configurado
❌ ERROR: SESSION_SECRET não configurado
❌ ERROR: dist/index.js não encontrado!
❌ ERROR: Uvicorn não está instalado!
```

**→ Se aparecer qualquer erro:** Me envie o erro completo

---

### ✅ Passo 2: Verificar se Container Está Rodando

**No Dokploy, aba "Terminal" ou "Shell":**

Execute:
```bash
# Ver containers rodando
docker ps

# Ver todos os containers (incluindo parados)
docker ps -a | grep o-conselho
```

**O que esperar:**
- Deve aparecer um container com status `Up` (rodando)
- Se aparecer `Exited` ou `Stopped`: container crashou

**→ Se container não estiver rodando:** Me envie o output completo

---

### ✅ Passo 3: Testar Health Check Dentro do Container

**No Dokploy, aba "Terminal" ou "Shell":**

Execute:
```bash
# Testar se aplicação responde
curl http://localhost:3001/api/health
```

#### ✅ SUCESSO - Deve retornar:
```json
{
  "status": "ok",
  "node": "healthy",
  "python": "healthy",
  "timestamp": "2024-..."
}
```

#### ❌ ERRO - Se retornar:
```
curl: (7) Failed to connect to localhost port 3001: Connection refused
```

**→ Se não responder:** Aplicação não está rodando na porta 3001

---

### ✅ Passo 4: Verificar Processos Rodando

**No terminal do Dokploy:**

Execute:
```bash
# Ver processos Node
ps aux | grep node

# Ver processos Python
ps aux | grep uvicorn

# Ver o que está escutando na porta 3001
netstat -tlnp | grep 3001
# ou
ss -tlnp | grep 3001
```

**O que esperar:**
- Deve aparecer processo `node dist/index.js`
- Deve aparecer processo `uvicorn` na porta 5002
- Deve aparecer `0.0.0.0:3001` escutando

**→ Se não aparecer:** Me envie o output completo

---

### ✅ Passo 5: Verificar Variáveis de Ambiente

**No Dokploy, aba "Environment":**

Verifique se TODAS estas variáveis estão configuradas:

- ✅ `NODE_ENV=production`
- ✅ `PORT=3001` (ou removida - start.sh define automaticamente)
- ✅ `DATABASE_URL=postgresql://...`
- ✅ `ANTHROPIC_API_KEY=sk-proj-...`
- ✅ `SESSION_SECRET=...` (mínimo 32 caracteres)
- ✅ `PERPLEXITY_API_KEY=...` (se necessário)
- ✅ `YOUTUBE_API_KEY=...` (se necessário)
- ✅ `GEMINI_API_KEY=...` (se necessário)

**→ Se alguma estiver faltando:** Configure e faça restart

---

### ✅ Passo 6: Verificar Configuração do Domínio

**No Dokploy, aba "Domains":**

1. Clique no domínio para editar
2. Verifique:
   - **Path:** `/` (root)
   - **Port:** `3001` ✅
   - **Protocol:** `HTTP` (ou HTTPS se tiver certificado)

3. Se estiver tudo correto:
   - **Delete** o domínio
   - **Recrie** o domínio
   - Aguarde 1-2 minutos para Traefik atualizar

---

### ✅ Passo 7: Testar Acesso Direto (Bypass Traefik)

**No seu navegador ou terminal:**

Tente acessar diretamente pelo IP:
```
http://72.60.244.72:3001
```

**Se funcionar:**
- Aplicação está rodando corretamente
- Problema é com Traefik/proxy reverso

**Se não funcionar:**
- Aplicação não está acessível de fora do container
- Pode ser problema de firewall ou rede

---

## 🔧 SOLUÇÕES BASEADAS NO DIAGNÓSTICO

### Se Container Não Está Rodando:

1. Verifique os logs completos desde o início
2. Procure por erros de inicialização
3. Verifique variáveis de ambiente
4. Tente iniciar manualmente:
   ```bash
   docker start <CONTAINER_ID>
   docker logs -f <CONTAINER_ID>
   ```

---

### Se Container Está Rodando mas Health Check Não Funciona:

1. Verifique se Node está escutando em `0.0.0.0:3001`
2. Execute: `netstat -tlnp | grep 3001`
3. Deve aparecer: `0.0.0.0:3001` (não `127.0.0.1:3001`)

---

### Se Health Check Funciona mas Traefik Não Conecta:

1. Recrie o domínio no Dokploy
2. Aguarde alguns minutos para Traefik atualizar
3. Verifique se há configurações de firewall bloqueando

---

## 📋 CHECKLIST RÁPIDO

Execute e me envie os resultados:

- [ ] **Logs completos desde o início** (copie tudo após "Docker Deployed: ✅")
- [ ] **Output de:** `docker ps -a | grep o-conselho`
- [ ] **Output de:** `curl http://localhost:3001/api/health`
- [ ] **Output de:** `ps aux | grep node` e `ps aux | grep uvicorn`
- [ ] **Output de:** `netstat -tlnp | grep 3001`
- [ ] **Lista de variáveis de ambiente** (confirme se todas estão configuradas)

---

## 🆘 PRÓXIMOS PASSOS

**Execute TODOS os passos acima e me envie os resultados.**

Com essas informações, conseguirei identificar exatamente onde está o problema!

---

**IMPORTANTE:** Envie os logs COMPLETOS desde o início, não apenas as últimas linhas!

