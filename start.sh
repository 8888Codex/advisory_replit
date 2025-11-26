#!/bin/bash
set -e

echo "🚀 Iniciando O Conselho Marketing Advisory Platform"
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
mkdir -p attached_assets/avatars attached_assets/custom_experts logs backups
echo "✅ Diretórios criados"

# Inicializar banco de dados (criar tabelas se não existirem)
if [ -f "/app/init-db.sh" ]; then
    echo "🗄️  Executando inicialização do banco de dados..."
    bash /app/init-db.sh || echo "⚠️  Inicialização do banco falhou, continuando mesmo assim..."
fi

# Verificar se dist/index.js existe (build do Node)
if [ ! -f "dist/index.js" ]; then
    echo "❌ ERROR: dist/index.js não encontrado! O build falhou?"
    exit 1
fi

# Verificar se Python pode importar uvicorn
echo "🐍 Verificando dependências Python..."
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "❌ ERROR: Uvicorn não está instalado!"
    exit 1
fi
echo "✅ Dependências Python OK"

# Iniciar Python backend em background
echo "🐍 Iniciando Python backend (porta 5002)..."
cd /app/python_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 5002 --log-level info &
PYTHON_PID=$!
cd /app

echo "⏳ Aguardando Python backend inicializar..."

# Aguardar Python iniciar (até 60 segundos com feedback)
PYTHON_READY=false
for i in {1..60}; do
    # Tentar curl primeiro, se não disponível usar python ou wget
    if command -v curl >/dev/null 2>&1; then
        if curl -s http://localhost:5002/api/health > /dev/null 2>&1; then
            echo "✅ Python backend pronto! (PID: $PYTHON_PID)"
            PYTHON_READY=true
            break
        fi
    elif command -v python3 >/dev/null 2>&1; then
        if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/api/health')" >/dev/null 2>&1; then
            echo "✅ Python backend pronto! (PID: $PYTHON_PID)"
            PYTHON_READY=true
            break
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q -O /dev/null http://localhost:5002/api/health 2>/dev/null; then
            echo "✅ Python backend pronto! (PID: $PYTHON_PID)"
            PYTHON_READY=true
            break
        fi
    else
        # Se nenhum comando disponível, apenas verificar se processo está rodando
        if kill -0 $PYTHON_PID 2>/dev/null; then
            # Aguardar um pouco mais e assumir que está pronto
            if [ $i -gt 10 ]; then
                echo "✅ Python backend iniciado (PID: $PYTHON_PID) - assumindo pronto após 10s"
                PYTHON_READY=true
                break
            fi
        fi
    fi
    
    # Verificar se processo Python ainda está rodando
    if ! kill -0 $PYTHON_PID 2>/dev/null; then
        echo "❌ Python backend crashou durante inicialização!"
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
    echo "📋 Últimas linhas do log Python:"
    tail -n 20 /app/logs/backend.log 2>/dev/null || echo "(log não disponível)"
    kill $PYTHON_PID 2>/dev/null || true
    exit 1
fi

# Iniciar Node server (foreground)
echo "🟢 Iniciando Node server (porta 3001)..."
echo "=================================================="

# Garantir que se Node parar, Python também para
trap "echo '⚠️  Encerrando serviços...'; kill $PYTHON_PID 2>/dev/null || true; exit" INT TERM EXIT

# Definir PORT=3001 para o servidor Node
export PORT=3001

# Iniciar Node server
NODE_ENV=production PORT=3001 node dist/index.js

# Se chegamos aqui, Node parou - matar Python também
kill $PYTHON_PID 2>/dev/null || true
