# Deploy para Dokploy - O Conselho

Guia completo para fazer deploy da plataforma no Dokploy.

## Pré-requisitos

1. **Conta no Dokploy** configurada
2. **Variáveis de ambiente** preparadas (veja `ENV_VARIABLES.md`)
3. **Repositório Git** (GitHub, GitLab, ou Bitbucket)

---

## Passo 1: Preparar Variáveis de Ambiente

Antes do deploy, você precisa configurar as variáveis obrigatórias:

### Obrigatórias (Sistema não inicia sem elas)

```bash
DATABASE_URL=postgresql://user:password@host:port/database
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SESSION_SECRET=$(openssl rand -base64 32)
NODE_ENV=production
```

### Recomendadas (Funcionalidades adicionais)

```bash
PERPLEXITY_API_KEY=your-perplexity-key
YOUTUBE_API_KEY=your-youtube-key
REDIS_URL=redis://redis:6379
REDIS_ENABLED=true
```

---

## Passo 2: Configurar Projeto no Dokploy

### Via Interface Web

1. **Criar Novo Projeto**
   - Nome: `o-conselho`
   - Tipo: Docker Compose

2. **Conectar Repositório Git**
   - URL do repositório
   - Branch: `main`
   - Caminho: `advisory_replit/`

3. **Configurar Build**
   - Build Command: `docker-compose build`
   - Start Command: `docker-compose up -d`

4. **Adicionar Variáveis de Ambiente**
   - Cole todas as variáveis obrigatórias
   - Marque `SESSION_SECRET` como secreta
   - Marque `ANTHROPIC_API_KEY` como secreta

---

## Passo 3: Configurar Banco de Dados

Dokploy pode criar um PostgreSQL automaticamente:

### Opção A: Database Interno do Dokploy

1. Criar database `advisory`
2. Anotar credenciais geradas
3. Atualizar `DATABASE_URL` nas variáveis de ambiente

### Opção B: Database Externo

1. Use um PostgreSQL hospedado (Neon, Supabase, RDS, etc)
2. Configure `DATABASE_URL` com a connection string
3. Execute a migration de soft delete:

```bash
psql $DATABASE_URL < add_soft_delete.sql
```

---

## Passo 4: Configurar Redis (Opcional)

Para melhor performance, habilite Redis:

1. No Dokploy, adicione serviço Redis ao projeto
2. Configure variáveis:
   ```bash
   REDIS_URL=redis://redis:6379
   REDIS_ENABLED=true
   ```

---

## Passo 5: Deploy

### Primeiro Deploy

```bash
# 1. Push seu código para Git
git add .
git commit -m "feat: production ready with all security features"
git push origin main

# 2. No Dokploy, clique em "Deploy"
# 3. Aguarde build e startup (5-10 minutos)
# 4. Verifique logs
```

### Verificar Saúde do Sistema

```bash
# Health check
curl https://seu-dominio.com/api/health

# Deve retornar:
{
  "status": "healthy",
  "database": "connected",
  "pool": { ... }
}
```

---

## Passo 6: Configurar Backup Automático

### No Dokploy

1. Vá em Settings > Backups
2. Enable automatic backups
3. Schedule: `0 2 * * *` (2 AM daily)
4. Retention: 30 days

### Backup Manual

```bash
# SSH no container
dokploy exec o-conselho app

# Executar backup
./backup_db.sh

# Download backup
dokploy download o-conselho /app/backups/backup_latest.sql.gz
```

---

## Passo 7: Configurar Domínio e SSL

1. **Adicionar Domínio**
   - No Dokploy: Settings > Domains
   - Adicionar: `o-conselho.seudominio.com`

2. **Habilitar SSL**
   - Dokploy configura Let's Encrypt automaticamente
   - Aguardar certificado ser emitido (~2 minutos)

3. **Testar HTTPS**
   ```bash
   curl https://o-conselho.seudominio.com/api/health
   ```

---

## Passo 8: Monitoramento

### Logs

```bash
# Ver logs em tempo real
dokploy logs o-conselho app -f

# Ver logs do Python backend
dokploy logs o-conselho app | grep "INFO"

# Ver apenas erros
dokploy logs o-conselho app | grep "ERROR"
```

### Métricas

1. Acesse dashboard do Dokploy
2. Vá em Monitoring
3. Configure alertas:
   - CPU > 80%
   - Memory > 90%
   - Health check failures > 3

### Error Tracking (Opcional)

Se configurou Sentry:
1. Adicione `SENTRY_DSN` nas variáveis
2. Erros serão enviados automaticamente
3. Acesse dashboard do Sentry para ver stack traces

---

## Troubleshooting

### Build Falha

```bash
# Ver logs detalhados
dokploy logs build o-conselho

# Problemas comuns:
# - Variável de ambiente faltando
# - Dependência não instalada
# - Espaço em disco insuficiente
```

### App Não Inicia

```bash
# Verificar health check
curl http://localhost:3001/api/health

# Verificar logs
dokploy logs o-conselho app --tail=100

# Verificar variáveis de ambiente
dokploy env list o-conselho
```

### Database Connection Errors

```bash
# Testar conexão com database
dokploy exec o-conselho app psql $DATABASE_URL -c "SELECT 1"

# Verificar pool status
curl http://localhost:3001/api/health | jq '.pool'
```

### Rate Limit Issues

```bash
# Limpar rate limits (desenvolvimento apenas)
dokploy exec o-conselho postgres psql -U postgres -d advisory \
  -c "DELETE FROM rate_limit_login; DELETE FROM rate_limit_register;"
```

---

## Rollback

Se houver problemas:

```bash
# Reverter para versão anterior
dokploy rollback o-conselho

# Ou fazer deploy de um commit específico
dokploy deploy o-conselho --commit=abc123
```

---

## Scaling

### Vertical Scaling (Mais recursos)

1. Dokploy > Settings > Resources
2. Aumentar CPU/Memory

### Horizontal Scaling (Múltiplas instâncias)

1. Dokploy > Settings > Scaling
2. Min instances: 2
3. Max instances: 5
4. Auto-scale baseado em CPU/Memory

**Nota**: Horizontal scaling requer Redis para sessões compartilhadas!

---

## Backups e Disaster Recovery

### Backup Manual Antes de Mudanças Grandes

```bash
# Backup completo
./backup_db.sh ./backups

# Fazer snapshot do volume
dokploy snapshot create o-conselho postgres_data
```

### Restaurar Backup

```bash
# 1. Download backup
dokploy download o-conselho /app/backups/backup_YYYY-MM-DD.sql.gz

# 2. Descompactar e restaurar
gunzip backup_YYYY-MM-DD.sql.gz
psql $DATABASE_URL < backup_YYYY-MM-DD.sql
```

---

## Checklist Pós-Deploy

- [ ] Health check retorna "healthy"
- [ ] Login funciona
- [ ] Criar persona e enriquecer
- [ ] Chat 1:1 com especialista
- [ ] Análise do Council
- [ ] Upload de avatar
- [ ] Verificar logs estruturados
- [ ] Testar rate limiting
- [ ] Backup automático configurado
- [ ] SSL ativo
- [ ] Monitoramento ativo

---

## Contato e Suporte

- Documentação Dokploy: https://docs.dokploy.com/
- Logs estruturados em: `/app/logs/`
- Health check: `https://seu-dominio.com/api/health`

---

## Performance Esperada

- **Startup**: ~30-40 segundos
- **Health Check**: < 100ms
- **Chat 1:1**: 2-5 segundos
- **Council Analysis**: 30-60 segundos
- **Persona Enrichment**: 2-5 minutos

---

✅ **Sistema pronto para produção!**

