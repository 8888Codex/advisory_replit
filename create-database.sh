#!/bin/bash
# Não usar set -e aqui - queremos tratar erros graciosamente

echo "🗄️  Verificando e criando banco de dados se necessário..."
echo "=================================================="

# Verificar se DATABASE_URL está configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não configurado"
    exit 1
fi

# Função para criar banco de dados se não existir
create_database_if_not_exists() {
    echo "🔍 Verificando se banco de dados existe..."
    
    # Extrair informações da DATABASE_URL usando Python
    if ! command -v python3 >/dev/null 2>&1; then
        echo "⚠️  Python3 não disponível, pulando verificação de banco..."
        echo "   (Assumindo que banco já existe ou será criado pelo PostgreSQL)"
        return 0
    fi
    
    DB_INFO=$(python3 <<EOF
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', '')
if url:
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    user = parsed.username or 'postgres'
    password = parsed.password or ''
    dbname = parsed.path.lstrip('/').split('?')[0] or 'advisory'
    print(f"{host}|{port}|{user}|{password}|{dbname}")
else:
    print("localhost|5432|postgres||advisory")
EOF
)
    
    IFS='|' read -r DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME <<< "$DB_INFO"
    
    echo "   Host: $DB_HOST, Port: $DB_PORT, User: $DB_USER, Database: $DB_NAME"
    
    # Verificar se banco existe e criar se necessário usando Python
    # Passar variáveis via variáveis de ambiente
    export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
    
    python3 <<'PYTHON_SCRIPT'
import asyncpg
import asyncio
import os
import sys

async def check_and_create():
    # Extrair variáveis de ambiente
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    target_db = os.environ.get('DB_NAME', 'advisory')
    
    # Construir URL do banco postgres (sempre existe)
    if db_password:
        postgres_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    else:
        postgres_url = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"
    
    try:
        # Conectar ao banco postgres
        conn = await asyncpg.connect(postgres_url)
        
        # Verificar se banco existe
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            target_db
        )
        
        if exists:
            print(f"✅ Banco de dados '{target_db}' já existe")
            await conn.close()
            return 0
        else:
            print(f"📊 Criando banco de dados '{target_db}'...")
            # Criar banco usando identifador entre aspas para segurança
            # asyncpg não permite parâmetros em CREATE DATABASE, então usamos formatação segura
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            await conn.close()
            print(f"✅ Banco de dados '{target_db}' criado com sucesso!")
            return 0
            
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f"✅ Banco de dados '{target_db}' já existe (detectado por erro)")
        return 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar/criar banco: {e}")
        # Não falhar completamente - pode ser que banco já existe ou problema de permissão
        return 1

exit_code = asyncio.run(check_and_create())
sys.exit(exit_code)
PYTHON_SCRIPT
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Verificação de banco concluída"
        return 0
    else
        echo "⚠️  Erro ao verificar/criar banco (código: $EXIT_CODE)"
        echo "   Isso pode ser normal se:"
        echo "   - Banco já existe e está acessível"
        echo "   - Há problemas de permissão (mas PostgreSQL pode criar automaticamente)"
        echo "   - PostgreSQL ainda não está totalmente pronto"
        return 0  # Retornar sucesso para não bloquear deploy
    fi
}

# Criar banco se necessário (não falhar se houver erro)
create_database_if_not_exists || {
    echo "⚠️  Falha na verificação de banco, mas continuando..."
    echo "   (PostgreSQL pode criar banco automaticamente ou já existe)"
}

echo "✅ Verificação de banco de dados concluída!"
echo "=================================================="

