# 🚀 Configurar Ambiente Local - O Conselho

## 📋 Opções para Rodar Localmente

### Opção 1: PostgreSQL Local (Recomendado para desenvolvimento)

#### Instalar PostgreSQL no macOS:

```bash
# Usando Homebrew
brew install postgresql@16
brew services start postgresql@16

# Criar banco de dados
createdb advisory

# Verificar se está rodando
pg_isready
```

#### Configurar `.env`:

```bash
DATABASE_URL=postgresql://$(whoami)@localhost:5432/advisory
```

---

### Opção 2: Docker (Mais fácil - tudo isolado)

#### Instalar Docker Desktop:

1. Baixe em: https://www.docker.com/products/docker-desktop/
2. Instale e inicie o Docker Desktop
3. Execute:

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
docker compose up postgres -d
```

Isso iniciará o PostgreSQL automaticamente!

---

### Opção 3: Banco de Dados em Nuvem (Mais rápido)

Use um banco de dados gratuito:

#### Neon (Recomendado - PostgreSQL gratuito):
1. Acesse: https://neon.tech
2. Crie uma conta gratuita
3. Crie um novo projeto
4. Copie a connection string
5. Cole no `.env`:

```bash
DATABASE_URL=postgresql://usuario:senha@host.neon.tech/advisory
```

#### Supabase (Alternativa):
1. Acesse: https://supabase.com
2. Crie um projeto gratuito
3. Vá em Settings → Database
4. Copie a connection string
5. Cole no `.env`

---

## 🚀 Iniciar Aplicação Local

### Passo 1: Configurar `.env`

Edite o arquivo `.env` na raiz do projeto:

```bash
# Database (escolha uma das opções acima)
DATABASE_URL=postgresql://usuario:senha@localhost:5432/advisory

# Anthropic API Key (OBRIGATÓRIO)
ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI

# Session Secret (já gerado)
SESSION_SECRET=m2U9O7OdRHpul42qysHwuWZs+ZNZiHGG7TD3DISmlFA=

# Environment
NODE_ENV=development
PORT=5001

# Python Backend Port
PYTHON_BACKEND_PORT=5002
```

### Passo 2: Instalar Dependências (se ainda não fez)

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit

# Node.js
npm install

# Python (se usar venv)
python3 -m venv .venv
source .venv/bin/activate
pip install -r <(python3 -c "import tomli; print('\n'.join(tomli.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" 2>/dev/null || echo "uvicorn fastapi anthropic asyncpg bcrypt crewai crewai-tools google-generativeai httpx loguru pillow pydantic python-dotenv redis requests resend tenacity youtube-transcript-api")
```

### Passo 3: Iniciar Aplicação

```bash
# Iniciar servidor (Node.js + Python backend automático)
npm run dev
```

A aplicação estará disponível em: **http://localhost:5001**

---

## 🔧 Troubleshooting

### Erro: "ECONNREFUSED" na porta 5432

**Solução:** PostgreSQL não está rodando

```bash
# Verificar se está rodando
pg_isready

# Se não estiver, iniciar:
brew services start postgresql@16
# ou
docker compose up postgres -d
```

### Erro: "DATABASE_URL environment variable is required"

**Solução:** Verifique se o arquivo `.env` existe e tem `DATABASE_URL` configurado

```bash
cat .env | grep DATABASE_URL
```

### Erro: "ANTHROPIC_API_KEY não configurado"

**Solução:** Adicione sua chave da API no `.env`

1. Obtenha em: https://console.anthropic.com/
2. Adicione no `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-sua-chave`

---

## ✅ Checklist

- [ ] PostgreSQL rodando (local, Docker ou nuvem)
- [ ] Arquivo `.env` configurado com `DATABASE_URL`
- [ ] `ANTHROPIC_API_KEY` configurada no `.env`
- [ ] Dependências Node.js instaladas (`npm install`)
- [ ] Dependências Python instaladas (se necessário)
- [ ] Servidor iniciado (`npm run dev`)
- [ ] Aplicação acessível em http://localhost:5001

---

## 🎯 Próximos Passos

Após tudo configurado:

1. Acesse http://localhost:5001
2. Crie uma conta ou faça login
3. Comece a usar a plataforma!

---

**Precisa de ajuda?** Verifique os logs em `/tmp/advisory_dev.log` ou no terminal onde rodou `npm run dev`

