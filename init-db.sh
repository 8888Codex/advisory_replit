#!/bin/bash
set -e

echo "🗄️  Inicializando banco de dados..."
echo "=================================================="

# Verificar se DATABASE_URL está configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não configurado"
    exit 1
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
        if command -v pg_isready >/dev/null 2>&1; then
            if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
                echo "✅ PostgreSQL está pronto!"
                return 0
            fi
        else
            # Se pg_isready não estiver disponível, tentar conexão direta com psql ou python
            if command -v psql >/dev/null 2>&1; then
                if PGPASSWORD=$(echo $DATABASE_URL | grep -oP '://[^:]+:\K[^@]+' || echo "") psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
                    echo "✅ PostgreSQL está pronto!"
                    return 0
                fi
            elif command -v python3 >/dev/null 2>&1; then
                # Tentar conexão com Python
                if python3 -c "
import asyncpg
import asyncio
import os
async def check():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.close()
        return True
    except:
        return False
exit(0 if asyncio.run(check()) else 1)
" 2>/dev/null; then
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
echo "   Executando: npm run db:push"

# Garantir que estamos no diretório correto
cd /app || cd "$(dirname "$0")/.." || pwd

# Executar drizzle-kit push
if npm run db:push 2>&1; then
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

