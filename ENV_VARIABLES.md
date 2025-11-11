# Environment Variables - O Conselho

## 🔴 Variáveis OBRIGATÓRIAS

Sistema não inicia sem estas variáveis:

### `DATABASE_URL`
- **Descrição**: Connection string do PostgreSQL
- **Formato**: `postgresql://user:password@host:port/database`
- **Exemplo**: `postgresql://postgres:mypassword@localhost:5432/advisory`

### `ANTHROPIC_API_KEY`
- **Descrição**: API key do Claude (Anthropic)
- **Obter em**: https://console.anthropic.com/
- **Formato**: `sk-ant-api03-...`

### `SESSION_SECRET`
- **Descrição**: Secret para criptografia de sessões
- **Requisito**: Mínimo 32 caracteres aleatórios
- **Gerar com**: `openssl rand -base64 32`
- **CRÍTICO**: Use valor único e forte em produção!

### `NODE_ENV`
- **Descrição**: Ambiente de execução
- **Valores**: `development` | `production` | `test`
- **Padrão**: `development`

---

## 🟡 Variáveis OPCIONAIS

Funcionalidades específicas (sistema funciona sem elas):

### APIs Externas

#### `PERPLEXITY_API_KEY`
- **Descrição**: API para pesquisa de mercado e enrichment
- **Obter em**: https://www.perplexity.ai/settings/api
- **Se ausente**: Pesquisa será pulada

#### `YOUTUBE_API_KEY`
- **Descrição**: YouTube Data API v3 para busca de vídeos
- **Obter em**: https://console.cloud.google.com/apis/credentials
- **Se ausente**: Vídeos não serão buscados

#### `UNSPLASH_ACCESS_KEY`
- **Descrição**: API para avatares de especialistas
- **Obter em**: https://unsplash.com/oauth/applications
- **Se ausente**: Avatares padrão serão usados

---

## ⚙️ Configurações Avançadas

Valores padrão já são adequados:

### Database Pool
```
DB_POOL_MIN_SIZE=5          # Dev: 5, Prod: 10-20
DB_POOL_MAX_SIZE=20         # Dev: 20, Prod: 50
DB_POOL_MAX_QUERIES=5000
```

### Anthropic API
```
ANTHROPIC_TIMEOUT=60
ANTHROPIC_MAX_RETRIES=3
ANTHROPIC_RETRY_DELAY=1
```

### Circuit Breaker
```
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=300
```

### Redis Cache (opcional)
```
REDIS_URL=
REDIS_ENABLED=false
```

### Logging
```
LOG_LEVEL=INFO              # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json             # json | text
```

### Rate Limiting
```
RATE_LIMIT_COUNCIL_PER_HOUR=10
RATE_LIMIT_ENRICHMENT_PER_DAY=3
RATE_LIMIT_AUTO_CLONE_PER_DAY=5
RATE_LIMIT_UPLOAD_PER_HOUR=10
```

### Upload Limits
```
MAX_UPLOAD_SIZE_MB=5
MAX_IMAGE_DIMENSION=2048
```

### Session
```
SESSION_MAX_AGE_HOURS=1
SESSION_ROLLING=true
```

### CORS (produção)
```
ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
```

---

## 🔧 Development Only

**NÃO usar em produção:**

```
CSRF_ENABLED=true           # SEMPRE true em produção
MOCK_PERPLEXITY=false
MOCK_YOUTUBE=false
MOCK_UNSPLASH=false
```

---

## 📊 Monitoramento

```
SENTRY_DSN=                 # Opcional, para error tracking
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *   # Cron: 2 AM diariamente
HEALTH_CHECK_ENABLED=true
```

---

## 🚀 Dokploy

```
PYTHON_BACKEND_PORT=5002
NODE_SERVER_PORT=3001
AUTO_START_PYTHON=true
```

---

## Criando arquivo .env

1. Crie arquivo `.env` na raiz do projeto
2. Copie e preencha as variáveis obrigatórias
3. **NUNCA** commite o arquivo `.env`

**Exemplo mínimo `.env`:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/advisory
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SESSION_SECRET=your-32-char-random-secret-here-change-this
NODE_ENV=development
```

