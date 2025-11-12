#!/bin/bash
set -e

echo "🚀 Iniciando O Conselho Marketing Advisory Platform (Replit)"
echo "=================================================="

# Verificar variáveis obrigatórias
echo "🔍 Verificando variáveis de ambiente..."

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não configurado"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY não configurado"
    exit 1
fi

if [ -z "$SESSION_SECRET" ]; then
    echo "❌ ERROR: SESSION_SECRET não configurado"
    exit 1
fi

echo "✅ Todas as variáveis obrigatórias configuradas"

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p attached_assets/avatars attached_assets/custom_experts attached_assets/user_avatars logs backups
echo "✅ Diretórios criados"

# Verificar se dist/index.js existe (build do Node)
if [ ! -f "dist/index.js" ]; then
    echo "⚠️  dist/index.js não encontrado! Fazendo build..."
    npm run build
fi

# Verificar se Python pode importar uvicorn
echo "🐍 Verificando dependências Python..."
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "⚠️  Uvicorn não encontrado! Instalando dependências Python..."
    pip install -q -r <(python3 -c "import tomli; print('\n'.join(tomli.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" 2>/dev/null || echo "uvicorn fastapi anthropic asyncpg bcrypt crewai crewai-tools google-generativeai httpx loguru pillow pydantic python-dotenv redis requests resend tenacity youtube-transcript-api")
fi
echo "✅ Dependências Python OK"

# Porta do Python backend (fixa para comunicação interna)
PYTHON_PORT=5002

# Porta do Node (usa PORT do Replit ou padrão 5000)
NODE_PORT=${PORT:-5000}

echo "🔌 Portas configuradas:"
echo "   - Python Backend: $PYTHON_PORT"
echo "   - Node Server: $NODE_PORT"

# Iniciar Python backend em background
echo "🐍 Iniciando Python backend (porta $PYTHON_PORT)..."
cd python_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port $PYTHON_PORT --log-level info > ../logs/python_backend.log 2>&1 &
PYTHON_PID=$!
cd ..

echo "⏳ Aguardando Python backend inicializar..."

# Aguardar Python iniciar (até 60 segundos)
PYTHON_READY=false
for i in {1..60}; do
    if curl -s http://localhost:$PYTHON_PORT/api/health > /dev/null 2>&1; then
        echo "✅ Python backend pronto! (PID: $PYTHON_PID)"
        PYTHON_READY=true
        break
    fi
    
    # Verificar se processo Python ainda está rodando
    if ! kill -0 $PYTHON_PID 2>/dev/null; then
        echo "❌ Python backend crashou durante inicialização!"
        echo "📋 Últimas linhas do log:"
        tail -n 20 logs/python_backend.log 2>/dev/null || echo "(log não disponível)"
        exit 1
    fi
    
    # Mostrar progresso a cada 10 segundos
    if [ $((i % 10)) -eq 0 ]; then
        echo "   ... ainda aguardando ($i/60s)"
    fi
    
    sleep 1
done

if [ "$PYTHON_READY" = false ]; then
    echo "❌ Python backend não iniciou em 60 segundos"
    echo "📋 Últimas linhas do log:"
    tail -n 20 logs/python_backend.log 2>/dev/null || echo "(log não disponível)"
    kill $PYTHON_PID 2>/dev/null || true
    exit 1
fi

# Garantir que se Node parar, Python também para
trap "echo '⚠️  Encerrando serviços...'; kill $PYTHON_PID 2>/dev/null || true; exit" INT TERM EXIT

# Iniciar Node server (foreground)
echo "🟢 Iniciando Node server (porta $NODE_PORT)..."
echo "=================================================="

# Definir variáveis de ambiente para Node
export PORT=$NODE_PORT
export PYTHON_BACKEND_PORT=$PYTHON_PORT
export NODE_ENV=production

# Iniciar Node server
node dist/index.js

# Se chegamos aqui, Node parou - matar Python também
kill $PYTHON_PID 2>/dev/null || true

