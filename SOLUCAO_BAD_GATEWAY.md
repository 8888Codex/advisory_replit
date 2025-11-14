# 🔧 Solução: Bad Gateway - Diagnóstico Passo a Passo

## ❌ Problema Persistente

Mesmo após corrigir o código para escutar em `0.0.0.0`, ainda recebe "Bad Gateway".

---

## 🔍 DIAGNÓSTICO PASSO A PASSO

### Passo 1: Verificar Logs da Aplicação

**No Dokploy:**

1. Vá na aba **"Logs"** da sua aplicação
2. Procure pelas últimas linhas (scroll até o final)
3. **O que procurar:**

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

#### ❌ ERRO - Se aparecer algo assim:
```
❌ ERROR: DATABASE_URL não configurado
```
ou
```
❌ ERROR: ANTHROPIC_API_KEY não configurado
```
ou
```
❌ ERROR: SESSION_SECRET não configurado
```
ou
```
❌ ERROR: dist/index.js não encontrado! O build falhou?
```

**→ Problema:** Variáveis de ambiente faltando ou build falhou

---

### Passo 2: Testar Health Check Dentro do Container

**No Dokploy:**

1. Vá na aba **"Terminal"** ou **"Shell"** da aplicação
2. Execute:

```bash
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

**→ Problema:** Aplicação não está rodando na porta 3001

---

### Passo 3: Verificar se o Processo Está Rodando

**No terminal do Dokploy, execute:**

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

**Esperado:**
- Deve ver um processo `node dist/index.js`
- Deve ver um processo `uvicorn main:app`
- Deve ver `0.0.0.0:3001` na lista de portas

---

### Passo 4: Verificar Variáveis de Ambiente

**No Dokploy:**

1. Vá na aba **"Environment"**
2. Verifique se TODAS estas variáveis estão configuradas:

**Obrigatórias:**
- ✅ `DATABASE_URL` - deve começar com `postgresql://`
- ✅ `ANTHROPIC_API_KEY` - deve começar com `sk-ant-`
- ✅ `SESSION_SECRET` - deve ter pelo menos 32 caracteres
- ✅ `NODE_ENV=production`

**Opcional mas recomendado:**
- `PORT=3001` (já está no start.sh, mas pode ajudar)

---

### Passo 5: Verificar Configuração do Domínio

**No Dokploy:**

1. Vá na aba **"Domains"**
2. Clique no ícone de **editar** (lápis) do domínio
3. Verifique:
   - **Path:** `/` (deve ser root)
   - **Port:** `3001` ✅
   - **Protocol:** `HTTP` (ou HTTPS se tiver certificado)

4. **Tente deletar e recriar o domínio:**
   - Delete o domínio atual
   - Clique em "Add Domain"
   - Configure:
     - Path: `/`
     - Port: `3001`
     - Protocol: `HTTP`
   - Salve
   - Aguarde 30-60 segundos para o Traefik atualizar

---

### Passo 6: Testar Acesso Direto (Bypass Traefik)

**No Dokploy, vá em Settings > Ports:**

1. Verifique se a porta **3001** está exposta publicamente
2. Se estiver, tente acessar diretamente:

```
http://72.60.244.72:3001
```

**Se funcionar diretamente:**
- O problema é com o Traefik/proxy
- Continue com Passo 7

**Se não funcionar:**
- O problema é com a aplicação
- Volte ao Passo 1 e verifique os logs

---

### Passo 7: Verificar Configuração do Traefik

O Dokploy usa Traefik como proxy reverso. Pode haver um problema de configuração.

**Soluções:**

1. **Recriar o domínio** (já mencionado no Passo 5)
2. **Verificar se há labels Traefik no docker-compose.yml**

   O Dokploy pode precisar de labels específicas. Verifique se há algo assim no `docker-compose.yml`:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.app.rule=Host(`seu-dominio.traefik.me`)"
  - "traefik.http.services.app.loadbalancer.server.port=3001"
```

   **Mas cuidado:** O Dokploy geralmente gerencia isso automaticamente.

3. **Verificar logs do Traefik** (se disponível no Dokploy)

---

## 🔧 SOLUÇÕES ESPECÍFICAS

### Solução A: Aplicação Não Está Iniciando

**Sintomas:**
- Logs mostram erro
- Health check não funciona
- Processo não está rodando

**Ações:**
1. Verifique variáveis de ambiente (Passo 4)
2. Verifique se o build foi bem-sucedido
3. Veja os logs completos desde o início

---

### Solução B: Aplicação Inicia mas Traefik Não Conecta

**Sintomas:**
- Logs mostram "serving on port 3001 (host: 0.0.0.0)"
- Health check funciona dentro do container
- Acesso direto funciona (`http://IP:3001`)
- Mas domínio retorna Bad Gateway

**Ações:**
1. Recriar o domínio (Passo 5)
2. Verificar configuração do Traefik
3. Aguardar alguns minutos (Traefik pode demorar para atualizar)

---

### Solução C: Porta Não Está Exposta

**Sintomas:**
- Aplicação está rodando
- Mas acesso direto não funciona

**Ações:**
1. No Dokploy: Settings > Ports
2. Adicione a porta 3001 manualmente
3. Faça rebuild

---

## 📋 CHECKLIST COMPLETO

Execute na ordem e marque cada item:

- [ ] **Logs mostram aplicação iniciando?**
  - Procure por "serving on port 3001 (host: 0.0.0.0)"
  
- [ ] **Health check funciona dentro do container?**
  - `curl http://localhost:3001/api/health` retorna JSON
  
- [ ] **Processo Node está rodando?**
  - `ps aux | grep node` mostra processo
  
- [ ] **Porta 3001 está escutando?**
  - `netstat -tlnp | grep 3001` mostra `0.0.0.0:3001`
  
- [ ] **Variáveis de ambiente configuradas?**
  - DATABASE_URL, ANTHROPIC_API_KEY, SESSION_SECRET, NODE_ENV
  
- [ ] **Acesso direto funciona?**
  - `http://72.60.244.72:3001` abre a aplicação
  
- [ ] **Domínio configurado corretamente?**
  - Port: 3001, Path: /
  
- [ ] **Domínio recriado?**
  - Delete e recrie o domínio

---

## 🆘 PRÓXIMOS PASSOS

**Me envie:**

1. **Últimas 50 linhas dos logs** (aba Logs no Dokploy)
2. **Resultado do health check** (`curl http://localhost:3001/api/health`)
3. **Resultado do acesso direto** (`http://72.60.244.72:3001`)
4. **Screenshot da configuração do domínio** (aba Domains)

Com essas informações, posso identificar exatamente o problema! 🔍

---

## 💡 DICA RÁPIDA

Se nada funcionar, tente:

1. **Deletar completamente a aplicação no Dokploy**
2. **Recriar do zero**
3. **Configurar variáveis de ambiente**
4. **Fazer deploy novamente**

Às vezes, recomeçar do zero resolve problemas de configuração do Traefik.

