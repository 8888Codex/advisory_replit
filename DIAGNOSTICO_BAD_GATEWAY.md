# 🔍 Diagnóstico: Bad Gateway - Traefik não consegue conectar

## ❌ Problema

**Erro:** `Bad Gateway` ao acessar o domínio  
**Causa:** Traefik (proxy reverso do Dokploy) não consegue se conectar à aplicação na porta 3001

---

## 🔍 VERIFICAÇÕES NECESSÁRIAS

### 1. Verificar Logs da Aplicação

No Dokploy:
1. Vá na aba **"Logs"**
2. Procure por estas mensagens:

**✅ Deve aparecer:**
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

**❌ Se aparecer erro:**
- Procure por mensagens de erro
- Verifique se Python iniciou corretamente
- Verifique se Node iniciou corretamente

---

### 2. Verificar se a Aplicação Está Escutando Corretamente

O problema pode ser que o servidor Node está escutando apenas em `localhost` ao invés de `0.0.0.0`.

**No Docker, o servidor DEVE escutar em `0.0.0.0` para ser acessível de fora do container.**

Verifique no código `server/index.ts` linha ~1316:

```typescript
server.listen(port, () => {
  log(`serving on port ${port}`);
});
```

**Deve ser:**
```typescript
server.listen(port, '0.0.0.0', () => {
  log(`serving on port ${port}`);
});
```

---

### 3. Testar Health Check Diretamente

No Dokploy, vá na aba **"Terminal"** ou **"Shell"** e execute:

```bash
# Testar se a aplicação responde dentro do container
curl http://localhost:3001/api/health
```

**Esperado:**
```json
{
  "status": "ok",
  "node": "healthy",
  "python": "healthy",
  "timestamp": "2024-..."
}
```

**Se não responder:**
- A aplicação não está rodando
- Verifique os logs para ver o erro

---

### 4. Verificar Porta Exposta no Container

No Dokploy:
1. Vá em **Settings** > **Ports** (ou **General**)
2. Verifique se a porta **3001** está exposta
3. Se não estiver, adicione manualmente

---

## 🔧 SOLUÇÕES POSSÍVEIS

### Solução 1: Corrigir Bind do Servidor Node

Se o servidor está escutando apenas em `localhost`, precisa escutar em `0.0.0.0`:

**Arquivo:** `server/index.ts` (linha ~1316)

**Mudar de:**
```typescript
server.listen(port, () => {
  log(`serving on port ${port}`);
});
```

**Para:**
```typescript
server.listen(port, '0.0.0.0', () => {
  log(`serving on port ${port}`);
});
```

Depois:
1. Commit e push
2. Rebuild no Dokploy

---

### Solução 2: Verificar Variáveis de Ambiente

No Dokploy, vá em **Environment** e verifique:

**Obrigatórias:**
- ✅ `DATABASE_URL` - configurado
- ✅ `ANTHROPIC_API_KEY` - configurado
- ✅ `SESSION_SECRET` - configurado (mínimo 32 caracteres)
- ✅ `NODE_ENV=production` - configurado
- ✅ `PORT=3001` - configurado (opcional, já está no start.sh)

---

### Solução 3: Verificar se Python Backend Está Rodando

No terminal do Dokploy, execute:

```bash
# Verificar se Python está rodando
ps aux | grep uvicorn

# Ou testar diretamente
curl http://localhost:5002/api/health
```

**Se Python não estiver rodando:**
- Verifique os logs para ver o erro
- Pode ser problema com dependências Python
- Pode ser problema com variáveis de ambiente

---

### Solução 4: Verificar Configuração do Traefik

No Dokploy, na aba **Domains**:

1. Clique no ícone de **editar** do domínio
2. Verifique:
   - **Path:** `/` (deve ser root)
   - **Port:** `3001` ✅ (já corrigido)
   - **Protocol:** `HTTP` (ou HTTPS se tiver certificado)

3. Se estiver tudo correto, tente:
   - **Deletar** o domínio
   - **Recriar** o domínio
   - Aguardar alguns segundos para o Traefik atualizar

---

### Solução 5: Verificar Firewall/Network

Se nada funcionar, pode ser problema de rede:

1. No Dokploy, verifique se há configurações de firewall
2. Verifique se a porta 3001 está aberta
3. Tente acessar diretamente via IP: `http://72.60.244.72:3001`

---

## 📋 CHECKLIST DE DIAGNÓSTICO

Execute na ordem:

- [ ] **Logs mostram aplicação iniciando?**
  - Procure por "serving on port 3001"
  
- [ ] **Health check funciona dentro do container?**
  - `curl http://localhost:3001/api/health`
  
- [ ] **Python backend está rodando?**
  - `curl http://localhost:5002/api/health`
  
- [ ] **Servidor Node escuta em 0.0.0.0?**
  - Verificar código `server/index.ts`
  
- [ ] **Porta 3001 está exposta?**
  - Settings > Ports
  
- [ ] **Domínio configurado corretamente?**
  - Port: 3001, Path: /
  
- [ ] **Variáveis de ambiente configuradas?**
  - DATABASE_URL, ANTHROPIC_API_KEY, SESSION_SECRET

---

## 🆘 PRÓXIMOS PASSOS

1. **Verifique os logs primeiro** - isso vai mostrar o problema real
2. **Teste o health check dentro do container** - confirma se a aplicação está rodando
3. **Verifique se o servidor escuta em 0.0.0.0** - crítico para Docker
4. **Se necessário, faça rebuild** após corrigir o código

---

**Me envie os logs da aplicação para eu ajudar melhor!** 📋

