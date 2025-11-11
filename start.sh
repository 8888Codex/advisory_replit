#!/bin/bash
set -e

echo "🚀 Iniciando O Conselho Marketing Advisory Platform"
echo "=================================================="

# Verificar variáveis obrigatórias
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

echo "✅ Variáveis de ambiente validadas"

# Criar diretórios necessários
mkdir -p attached_assets/avatars attached_assets/custom_experts logs backups
echo "✅ Diretórios criados"

# Iniciar Python backend em background
echo "🐍 Iniciando Python backend (porta 5002)..."
cd python_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 5002 &
PYTHON_PID=$!
cd ..

# Aguardar Python iniciar (até 30 segundos)
echo "⏳ Aguardando Python backend inicializar..."
for i in {1..30}; do
    if curl -s http://localhost:5002/api/health > /dev/null 2>&1; then
        echo "✅ Python backend pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Python backend não iniciou a tempo"
        exit 1
    fi
    sleep 1
done

# Iniciar Node server (foreground)
echo "🟢 Iniciando Node server (porta 3001)..."
NODE_ENV=production node dist/index.js

# Se o Node parar, matar Python também
kill $PYTHON_PID 2>/dev/null || true

