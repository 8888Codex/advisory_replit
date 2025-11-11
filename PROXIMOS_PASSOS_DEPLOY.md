# 🚀 Próximos Passos para Deploy

Todas as melhorias de produção foram implementadas! Agora siga estes passos para fazer o deploy no Dokploy.

---

## Passo 1: Instalar Novas Dependências

### Python
```bash
cd advisory_replit
uv pip install --system .
# ou
pip install -e .[test]
```

**Novas dependências**:
- `loguru` - Logging estruturado
- `redis` - Cache
- `tenacity` - Retry logic
- `pytest`, `pytest-asyncio`, `pytest-cov` - Testes

### Node.js
```bash
npm install
```

**Novas dependências**:
- `csurf` - CSRF protection
- `@types/csurf` - Types

---

## Passo 2: Aplicar Migration de Soft Delete

```bash
# Conectar ao banco local
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/advisory"

# Aplicar migration
psql $DATABASE_URL < add_soft_delete.sql
```

**O que faz**:
- Adiciona coluna `deleted_at` em 4 tabelas
- Cria índices para performance
- Habilita soft delete (não perde dados)

---

## Passo 3: Testar Localmente (Opcional mas Recomendado)

### Rodar Testes
```bash
./run_tests.sh
```

**Espera-se**: Todos os testes passam ✅

### Testar com Docker
```bash
docker-compose build
docker-compose up -d

# Verificar health
curl http://localhost:3001/api/health

# Ver logs
docker-compose logs -f app
```

---

## Passo 4: Preparar Variáveis de Ambiente para Produção

Crie uma lista segura de todas as variáveis (use gerenciador de senhas):

```bash
# OBRIGATÓRIAS
DATABASE_URL=postgresql://user:pass@host:port/database
ANTHROPIC_API_KEY=sk-ant-api03-...
SESSION_SECRET=$(openssl rand -base64 32)
NODE_ENV=production

# OPCIONAIS (recomendadas)
PERPLEXITY_API_KEY=pplx-...
YOUTUBE_API_KEY=AIza...
REDIS_URL=redis://redis:6379
REDIS_ENABLED=true

# CONFIGURAÇÕES (usar padrões ou ajustar)
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
LOG_LEVEL=INFO
```

⚠️ **IMPORTANTE**: 
- Gere um **novo** SESSION_SECRET para produção
- **NUNCA** use os mesmos secrets de desenvolvimento

---

## Passo 5: Commit e Push

```bash
git add .
git commit -m "feat: production ready - security, resilience, monitoring"
git push origin main
```

---

## Passo 6: Configurar no Dokploy

### 6.1 Criar Projeto
1. Login no Dokploy
2. **Novo Projeto** → Nome: `o-conselho`
3. **Tipo**: Docker Compose

### 6.2 Conectar Git
1. **Repository URL**: seu-repositorio.git
2. **Branch**: main
3. **Path**: `advisory_replit/`

### 6.3 Adicionar Database
1. **Add Service** → PostgreSQL
2. Nome: `advisory-postgres`
3. Versão: 16
4. **Anotar** as credenciais geradas

### 6.4 Adicionar Redis (Opcional)
1. **Add Service** → Redis
2. Nome: `advisory-redis`
3. Versão: 7

### 6.5 Configurar Variáveis de Ambiente
Cole TODAS as variáveis da lista do Passo 4.

**Marcar como "Secret"**:
- `SESSION_SECRET`
- `ANTHROPIC_API_KEY`
- `PERPLEXITY_API_KEY`
- `DATABASE_URL`

### 6.6 Configurar Build
- **Build Command**: `docker-compose build`
- **Start Command**: `docker-compose up -d`
- **Health Check Path**: `/api/health`
- **Port**: 3001

---

## Passo 7: Fazer Deploy

1. Clique em **Deploy**
2. Aguarde build (5-10 minutos)
3. Monitore logs em tempo real
4. Aguarde health check passar

---

## Passo 8: Configurar Domínio e SSL

1. **Settings** → **Domains**
2. Adicionar: `o-conselho.seudominio.com`
3. Habilitar SSL (Let's Encrypt automático)
4. Aguardar certificado (~2min)

---

## Passo 9: Verificar Sistema

### Health Check
```bash
curl https://o-conselho.seudominio.com/api/health
```

**Esperado**:
```json
{
  "status": "healthy",
  "database": "connected",
  "pool": {
    "size": 10,
    "free": 9,
    "in_use": 1
  }
}
```

### Testar Funcionalidades
- [ ] Acessar aplicação
- [ ] Fazer login
- [ ] Criar persona
- [ ] Enriquecer persona
- [ ] Chat 1:1 com especialista
- [ ] Análise do Council
- [ ] Upload de avatar

---

## Passo 10: Configurar Backups

### Backup Automático via Dokploy
1. **Settings** → **Backups**
2. **Enable**: ON
3. **Schedule**: `0 2 * * *` (2 AM diário)
4. **Retention**: 30 days

### Testar Backup Manual
```bash
# SSH no container
dokploy exec o-conselho app bash

# Executar backup
./backup_db.sh

# Verificar arquivo criado
ls -lh backups/
```

---

## Passo 11: Configurar Monitoramento

### Logs
```bash
# Ver logs em tempo real
dokploy logs o-conselho app -f

# Filtrar por nível
dokploy logs o-conselho app | grep "ERROR"
dokploy logs o-conselho app | grep "WARNING"
```

### Alertas (Opcional)
1. **Monitoring** → **Alerts**
2. Configurar:
   - CPU > 80% por 5min
   - Memory > 90% por 5min
   - Health check failures > 3
   - Disk space < 10%

### Sentry (Opcional)
Se tiver Sentry:
1. Criar projeto no Sentry
2. Obter DSN
3. Adicionar variável: `SENTRY_DSN=https://...@sentry.io/...`
4. Re-deploy

---

## Troubleshooting Comum

### Build Falha
```bash
# Ver logs detalhados
dokploy logs build o-conselho

# Causas comuns:
# - Variável de ambiente faltando → verificar ENV_VARIABLES.md
# - Dependência não instalada → verificar pyproject.toml e package.json
```

### App Não Inicia
```bash
# Verificar validação de env vars
dokploy logs o-conselho app | grep "VALIDANDO"

# Se falhar validação, ajustar variáveis em Settings → Environment
```

### Rate Limit em Produção
```bash
# Limpar rate limit de um usuário específico (admin apenas)
dokploy exec o-conselho postgres psql -U postgres -d advisory -c \
  "DELETE FROM rate_limit_login WHERE key='IP_OU_USER_ID'"
```

---

## 📊 Monitoramento Pós-Deploy (Primeiras 24h)

### Métricas para Acompanhar
- [ ] Health check sempre "healthy"
- [ ] Response time médio < 3s
- [ ] Database pool: conexões livres > 50%
- [ ] Circuit breakers: estado CLOSED
- [ ] Zero erros 500
- [ ] Rate limits: nenhum bloqueio legítimo
- [ ] Backup automático executado
- [ ] Logs estruturados sendo gravados

### Dashboard Dokploy
- CPU usage
- Memory usage
- Network traffic
- Disk space

---

## 🎯 Critérios de Sucesso

### Funcional
- ✅ Todos os endpoints respondendo
- ✅ Usuários conseguem fazer login
- ✅ Personas enriquecendo corretamente
- ✅ Chat 1:1 e Council funcionando
- ✅ Upload de arquivos seguro

### Performance
- ✅ Health check < 100ms
- ✅ Chat response < 5s
- ✅ Council analysis < 60s
- ✅ Database pool healthy

### Segurança
- ✅ SSL ativo
- ✅ Rate limiting funcionando
- ✅ File uploads validados
- ✅ Sessions seguras
- ✅ Logs não expõem secrets

### Resiliência
- ✅ Retry em falhas transientes
- ✅ Circuit breakers protegendo
- ✅ Backups automáticos
- ✅ Soft delete preservando dados

---

## 🎉 Pronto para Produção!

Após seguir estes passos, seu sistema estará rodando em produção com:

- 🔒 **Segurança de nível empresarial**
- 🛡️ **Resiliência contra falhas**
- 📊 **Observabilidade completa**
- ⚡ **Performance otimizada**
- 🧪 **Qualidade testada**

**Boa sorte com o deploy!** 🚀

---

**Documentação Relacionada**:
- `ENV_VARIABLES.md` - Todas as variáveis de ambiente
- `DEPLOY_DOKPLOY.md` - Guia detalhado de deploy
- `PRODUCTION_READY_SUMMARY.md` - Resumo técnico completo
- `PRIORIDADES_DEPLOY.md` - Análise original de prioridades

