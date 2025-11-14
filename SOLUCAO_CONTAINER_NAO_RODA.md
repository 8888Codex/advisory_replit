# 🔧 Solução: Container Não Está Rodando

## ❌ Problema Identificado

**Erro:** `container is not running`  
**Sintoma:** `ERR_CONNECTION_REFUSED` ao acessar `http://72.60.244.72:3001`

**Causa:** O container Docker foi criado mas não está rodando (provavelmente crashou ao iniciar).

---

## 🔍 DIAGNÓSTICO

### Passo 1: Verificar Logs do Container (CRÍTICO)

**No Dokploy:**

1. Vá na aba **"Logs"** da aplicação
2. Veja TODOS os logs (não apenas os últimos)
3. Procure por erros no início

**Erros comuns:**

#### ❌ Erro 1: Variáveis de Ambiente Faltando
```
❌ ERROR: DATABASE_URL não configurado
❌ ERROR: ANTHROPIC_API_KEY não configurado
❌ ERROR: SESSION_SECRET não configurado
```

**Solução:** Configure as variáveis de ambiente no Dokploy (aba Environment)

---

#### ❌ Erro 2: Python Backend Não Inicia
```
❌ ERROR: Uvicorn não está instalado!
❌ Python backend crashou durante inicialização!
```

**Solução:** Verificar se dependências Python foram instaladas corretamente

---

#### ❌ Erro 3: Node Server Não Inicia
```
❌ ERROR: dist/index.js não encontrado! O build falhou?
```

**Solução:** Verificar se o build do frontend foi concluído

---

#### ❌ Erro 4: Conexão com Banco de Dados
```
❌ ERROR: Connection refused to database
❌ ERROR: Database connection failed
```

**Solução:** Verificar `DATABASE_URL` e se o PostgreSQL está rodando

---

### Passo 2: Verificar Status do Container

**No Dokploy, aba "Terminal" ou "Shell":**

Execute:
```bash
# Ver status do container
docker ps -a | grep o-conselho

# Ou ver todos os containers
docker ps -a
```

**Procure por:**
- Container com status `Exited` ou `Stopped`
- Exit code diferente de 0 (indica erro)

---

### Passo 3: Tentar Iniciar o Container Manualmente

**No terminal do Dokploy:**

```bash
# Ver o ID do container
docker ps -a | grep o-conselho

# Tentar iniciar
docker start <CONTAINER_ID>

# Ver logs em tempo real
docker logs -f <CONTAINER_ID>
```

**Se crashar imediatamente:**
- Veja os logs para identificar o erro
- Provavelmente é problema com variáveis de ambiente ou dependências

---

## 🔧 SOLUÇÕES ESPECÍFICAS

### Solução A: Variáveis de Ambiente Faltando

**Sintomas:**
- Logs mostram `❌ ERROR: [VARIAVEL] não configurado`
- Container para imediatamente após iniciar

**Ações:**

1. No Dokploy, vá em **Environment**
2. Adicione TODAS estas variáveis:

**Obrigatórias:**
```bash
DATABASE_URL=postgresql://user:password@host:port/database
ANTHROPIC_API_KEY=sk-ant-api03-...
SESSION_SECRET=seu-secret-minimo-32-caracteres-aqui
NODE_ENV=production
```

3. Salve
4. Faça **restart** da aplicação (não rebuild, apenas restart)

---

### Solução B: Banco de Dados Não Conecta

**Sintomas:**
- Logs mostram erro de conexão com banco
- Container para após tentar conectar

**Ações:**

1. Verifique se o PostgreSQL está rodando no Dokploy
2. Verifique se `DATABASE_URL` está correto:
   - Formato: `postgresql://user:password@host:port/database`
   - Host deve ser o nome do serviço PostgreSQL no Dokploy
   - Exemplo: `postgresql://postgres:senha@postgres:5432/advisory`

3. Teste a conexão:
   ```bash
   # No terminal do Dokploy
   psql $DATABASE_URL -c "SELECT 1"
   ```

---

### Solução C: Dependências Não Instaladas

**Sintomas:**
- Logs mostram `Module not found` ou `Command not found`
- Python ou Node não encontram pacotes

**Ações:**

1. Verifique se o build foi completo (parece que sim, pelo log anterior)
2. Verifique se os arquivos foram copiados:
   ```bash
   # No terminal do container
   ls -la /app/dist/index.js
   ls -la /app/python_backend/main.py
   ```

3. Se faltar arquivos, faça rebuild completo

---

### Solução D: Porta Já em Uso

**Sintomas:**
- Logs mostram `EADDRINUSE` ou `port already in use`
- Container não consegue escutar na porta 3001

**Ações:**

1. Verifique se há outro container usando a porta:
   ```bash
   docker ps | grep 3001
   ```

2. Pare o container conflitante ou mude a porta

---

## 📋 CHECKLIST DE VERIFICAÇÃO

Execute na ordem:

- [ ] **Logs mostram erro específico?**
  - Identifique qual erro aparece primeiro
  
- [ ] **Variáveis de ambiente configuradas?**
  - DATABASE_URL, ANTHROPIC_API_KEY, SESSION_SECRET, NODE_ENV
  
- [ ] **PostgreSQL está rodando?**
  - Verifique no Dokploy se o serviço PostgreSQL está ativo
  
- [ ] **Container pode ser iniciado manualmente?**
  - `docker start <CONTAINER_ID>` funciona?
  
- [ ] **Logs mostram onde para?**
  - Veja a última linha antes do container parar

---

## 🆘 PRÓXIMOS PASSOS

**Envie-me:**

1. **Logs COMPLETOS do container** (não apenas últimas linhas)
   - No Dokploy: Logs > Veja desde o início
   
2. **Status do container:**
   ```bash
   docker ps -a | grep o-conselho
   ```

3. **Tentativa de iniciar manualmente:**
   ```bash
   docker start <CONTAINER_ID>
   docker logs -f <CONTAINER_ID>
   ```
   - O que aparece nos logs?

4. **Variáveis de ambiente configuradas?**
   - Screenshot da aba Environment (sem mostrar valores sensíveis)

---

## 💡 DICA RÁPIDA

**Se o container crasha imediatamente:**

1. **Veja os logs desde o início** - o primeiro erro é o mais importante
2. **Verifique variáveis de ambiente** - 90% dos problemas são isso
3. **Teste iniciar manualmente** - verá o erro em tempo real

---

**O mais importante agora:** Envie os logs completos do container para eu identificar o erro exato! 📋

