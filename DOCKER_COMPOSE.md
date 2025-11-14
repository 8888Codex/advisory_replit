# 🐳 Docker Compose - Guia de Uso

Este documento explica como usar o `docker-compose.yml` para executar o **O Conselho Marketing Advisory Platform**.

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Arquivo `.env` configurado (veja seção abaixo)

## 🚀 Início Rápido

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis obrigatórias:

```bash
# OBRIGATÓRIAS
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SESSION_SECRET=your-32-character-random-secret-here

# PostgreSQL (opcional - valores padrão)
POSTGRES_DB=advisory
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432

# Portas (opcional - valores padrão)
NODE_PORT=3001
PYTHON_PORT=5002
```

**Gerar SESSION_SECRET:**
```bash
openssl rand -base64 32
```

### 2. Iniciar os Serviços

```bash
# Build e iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs apenas da aplicação
docker-compose logs -f app
```

### 3. Parar os Serviços

```bash
# Parar e remover containers
docker-compose down

# Parar e remover containers + volumes (⚠️ apaga dados do banco!)
docker-compose down -v
```

## 🎯 Serviços Disponíveis

### 1. PostgreSQL (`postgres`)
- **Porta**: 5432 (padrão)
- **Banco**: `advisory` (padrão)
- **Usuário**: `postgres` (padrão)
- **Senha**: Configurada via `POSTGRES_PASSWORD` no `.env`
- **Volume**: `postgres_data` (persistente)
- **Health Check**: Automático

### 2. Redis (`redis`) - Opcional
- **Porta**: 6379 (padrão)
- **Volume**: `redis_data` (persistente)
- **Uso**: Habilitar com profile `with-redis`

### 3. Aplicação Principal (`app`)
- **Node.js Server**: Porta 3001
- **Python Backend**: Porta 5002
- **Volumes**:
  - `./attached_assets` → Uploads e avatares
  - `./logs` → Logs da aplicação
  - `./backups` → Backups do banco

## 🔧 Comandos Úteis

### Build e Rebuild

```bash
# Build sem cache
docker-compose build --no-cache

# Rebuild apenas do serviço app
docker-compose build app

# Build e iniciar
docker-compose up -d --build
```

### Logs e Debugging

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f app
docker-compose logs -f postgres

# Ver últimas 100 linhas
docker-compose logs --tail=100 app

# Entrar no container da aplicação
docker-compose exec app bash

# Verificar status dos serviços
docker-compose ps
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL
docker-compose exec postgres psql -U postgres -d advisory

# Backup do banco
docker-compose exec postgres pg_dump -U postgres advisory > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U postgres advisory < backup.sql
```

### Redis (se habilitado)

```bash
# Conectar ao Redis CLI
docker-compose exec redis redis-cli

# Verificar status
docker-compose exec redis redis-cli ping
```

## 🎛️ Profiles

### Habilitar Redis

```bash
# Iniciar com Redis
docker-compose --profile with-redis up -d

# Parar com Redis
docker-compose --profile with-redis down
```

## 🔍 Health Checks

Todos os serviços possuem health checks configurados:

- **PostgreSQL**: Verifica se está pronto para conexões
- **Redis**: Verifica com `ping`
- **App**: Verifica endpoint `/api/health` na porta 3001

Verificar status:
```bash
docker-compose ps
```

## 📊 Monitoramento

### Verificar Recursos

```bash
# Uso de recursos dos containers
docker stats

# Informações detalhadas de um container
docker inspect advisory-app
```

### Logs Estruturados

Os logs são salvos em:
- Container: `/app/logs/`
- Host: `./logs/`

## 🔐 Segurança

### Variáveis Sensíveis

⚠️ **NUNCA** commite o arquivo `.env` no git!

Adicione ao `.gitignore`:
```
.env
.env.local
.env.*.local
```

### Senhas Fortes

Use senhas fortes em produção:
```bash
# Gerar senha aleatória
openssl rand -base64 32
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs app

# Verificar se portas estão em uso
lsof -i :3001
lsof -i :5002
lsof -i :5432

# Verificar variáveis de ambiente
docker-compose exec app env | grep ANTHROPIC
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está saudável
docker-compose ps postgres

# Ver logs do PostgreSQL
docker-compose logs postgres

# Testar conexão manualmente
docker-compose exec app python3 -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://postgres:postgres@postgres:5432/advisory'))"
```

### Rebuild completo

```bash
# Parar tudo
docker-compose down -v

# Remover imagens
docker-compose rm -f

# Rebuild completo
docker-compose build --no-cache
docker-compose up -d
```

### Limpar tudo (⚠️ apaga dados!)

```bash
# Parar e remover containers, volumes e redes
docker-compose down -v --remove-orphans

# Remover imagens também
docker rmi $(docker images | grep advisory | awk '{print $3}')
```

## 📝 Variáveis de Ambiente Completas

Veja `ENV_VARIABLES.md` para lista completa de variáveis disponíveis.

### Mínimas Obrigatórias

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
SESSION_SECRET=...
```

### Recomendadas para Produção

```bash
# Database
POSTGRES_PASSWORD=senha-forte-aqui

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
PERPLEXITY_API_KEY=...
YOUTUBE_API_KEY=...

# Security
SESSION_SECRET=senha-aleatoria-32-chars-minimo
CORS_ORIGIN=https://seu-dominio.com

# Logging
LOG_LEVEL=INFO
NODE_ENV=production
```

## 🚀 Deploy em Produção

### Checklist

- [ ] Arquivo `.env` configurado com valores de produção
- [ ] `SESSION_SECRET` gerado com `openssl rand -base64 32`
- [ ] `POSTGRES_PASSWORD` forte e único
- [ ] `CORS_ORIGIN` configurado com domínio correto
- [ ] Volumes persistentes configurados
- [ ] Backups automáticos configurados
- [ ] Health checks funcionando
- [ ] Logs sendo coletados

### Exemplo de `.env` para Produção

```bash
# Security
SESSION_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-prod-key
PERPLEXITY_API_KEY=prod-key-here

# Database
POSTGRES_DB=advisory_prod
POSTGRES_USER=advisory_user

# CORS
CORS_ORIGIN=https://app.example.com

# Environment
NODE_ENV=production
LOG_LEVEL=INFO
```

## 📚 Recursos Adicionais

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)

## 🆘 Suporte

Em caso de problemas:
1. Verifique os logs: `docker-compose logs -f`
2. Verifique o status: `docker-compose ps`
3. Consulte `ENV_VARIABLES.md` para variáveis
4. Consulte `README.md` para documentação geral

