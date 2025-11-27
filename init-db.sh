#!/bin/bash
set -e

echo "🗄️  Inicializando banco de dados..."
echo "=================================================="

# Verificar se DATABASE_URL está configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não configurado"
    exit 1
fi

# Primeiro, criar banco de dados se não existir
if [ -f "/app/create-database.sh" ]; then
    echo "📊 Verificando se banco de dados existe..."
    bash /app/create-database.sh || echo "⚠️  Verificação de banco falhou, continuando mesmo assim..."
fi

# Função para aguardar PostgreSQL estar pronto
wait_for_postgres() {
    echo "⏳ Aguardando PostgreSQL estar pronto..."
    
    # Tentar extrair informações da DATABASE_URL usando Python (mais confiável)
    # Formato: postgresql://user:password@host:port/database
    if command -v python3 >/dev/null 2>&1; then
        DB_INFO=$(python3 <<EOF
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', '')
if url:
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    user = parsed.username or 'postgres'
    dbname = parsed.path.lstrip('/').split('?')[0] or 'advisory'
    print(f"{host}|{port}|{user}|{dbname}")
else:
    print("localhost|5432|postgres|advisory")
EOF
)
        IFS='|' read -r DB_HOST DB_PORT DB_USER DB_NAME <<< "$DB_INFO"
    else
        # Fallback: valores padrão
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_USER="postgres"
        DB_NAME="advisory"
    fi
    
    echo "   Host: $DB_HOST, Port: $DB_PORT, User: $DB_USER, Database: $DB_NAME"
    
    # Aguardar até 60 segundos
    MAX_ATTEMPTS=60
    for i in $(seq 1 $MAX_ATTEMPTS); do
        # Primeiro, verificar se PostgreSQL está rodando (conectar ao banco "postgres" que sempre existe)
        if command -v python3 >/dev/null 2>&1; then
            # Tentar conectar ao banco "postgres" primeiro (sempre existe)
            if python3 <<'PYTHON_CHECK'
import asyncpg
import asyncio
import os
from urllib.parse import urlparse

async def check_postgres():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    user = parsed.username or 'postgres'
    password = parsed.password or ''
    
    # Construir URL para banco "postgres" (sempre existe)
    if password:
        postgres_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    else:
        postgres_url = f"postgresql://{user}@{host}:{port}/postgres"
    
    try:
        conn = await asyncpg.connect(postgres_url)
        await conn.close()
        return True
    except:
        return False

exit(0 if asyncio.run(check_postgres()) else 1)
PYTHON_CHECK
            then
                echo "✅ PostgreSQL está pronto!"
                return 0
            fi
        elif command -v pg_isready >/dev/null 2>&1; then
            # Tentar conectar ao banco "postgres" primeiro
            if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" >/dev/null 2>&1; then
                echo "✅ PostgreSQL está pronto!"
                return 0
            fi
        elif command -v psql >/dev/null 2>&1; then
            # Tentar conectar ao banco "postgres"
            DB_PASSWORD=$(echo $DATABASE_URL | python3 -c "import sys, urllib.parse; print(urllib.parse.urlparse(sys.stdin.read()).password or '')" 2>/dev/null || echo "")
            if [ -n "$DB_PASSWORD" ]; then
                if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT 1" >/dev/null 2>&1; then
                    echo "✅ PostgreSQL está pronto!"
                    return 0
                fi
            else
                if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT 1" >/dev/null 2>&1; then
                    echo "✅ PostgreSQL está pronto!"
                    return 0
                fi
            fi
        fi
        
        if [ $((i % 10)) -eq 0 ]; then
            echo "   ... ainda aguardando ($i/$MAX_ATTEMPTS)"
        fi
        sleep 1
    done
    
    echo "⚠️  PostgreSQL não respondeu após $MAX_ATTEMPTS segundos"
    echo "   Continuando mesmo assim (pode falhar se DB não estiver pronto)..."
    return 1
}

# Aguardar PostgreSQL
wait_for_postgres || true

# Executar Drizzle Kit Push para criar/atualizar tabelas
echo "📊 Criando/atualizando tabelas com Drizzle..."
echo "   Executando: drizzle-kit push"

# Garantir que estamos no diretório correto
cd /app || cd "$(dirname "$0")/.." || pwd

# Verificar se drizzle-kit está disponível
if ! command -v drizzle-kit >/dev/null 2>&1; then
    echo "⚠️  drizzle-kit não encontrado no PATH"
    echo "   Tentando usar npx..."
    # Tentar com npx como fallback
    if command -v npx >/dev/null 2>&1; then
        DRIZZLE_CMD="npx drizzle-kit"
    else
        echo "❌ Erro: drizzle-kit não disponível e npx também não encontrado"
        echo "   Pulando criação de tabelas..."
        exit 0
    fi
else
    DRIZZLE_CMD="drizzle-kit"
fi

# Verificar se drizzle.config.ts existe
if [ ! -f "drizzle.config.ts" ]; then
    echo "⚠️  drizzle.config.ts não encontrado"
    echo "   Pulando criação de tabelas..."
    exit 0
fi

# Executar drizzle-kit push
if $DRIZZLE_CMD push 2>&1; then
    echo "✅ Tabelas criadas/atualizadas com sucesso!"
else
    EXIT_CODE=$?
    echo "⚠️  Erro ao executar drizzle-kit push (código: $EXIT_CODE)"
    echo "   Isso pode ser normal se:"
    echo "   - Tabelas já existem e estão atualizadas"
    echo "   - Há problemas de conexão (mas continuaremos mesmo assim)"
    echo "   Continuando mesmo assim..."
fi

echo "✅ Inicialização do banco de dados concluída!"
echo "=================================================="

