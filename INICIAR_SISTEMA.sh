#!/bin/bash

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "         🚀 INICIANDO ADVISORY REPLIT SYSTEM 🚀"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Ir para o diretório do projeto
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo "📂 Diretório: $PROJECT_DIR"
echo ""

# Parar processos antigos
echo "🛑 Parando processos antigos..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "tsx.*server" 2>/dev/null
sleep 3
echo "   ✅ Processos antigos encerrados"
echo ""

# Iniciar Python Backend
echo "🐍 Iniciando Python Backend (porta 5001)..."
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
cd python_backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 5001 > /tmp/python_backend.log 2>&1 &
PYTHON_PID=$!
cd ..
echo "   ✅ Python Backend iniciado (PID: $PYTHON_PID)"
sleep 8
echo ""

# Iniciar Frontend Node.js
echo "🌐 Iniciando Frontend Node.js (porta 3000)..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend iniciado (PID: $FRONTEND_PID)"
echo ""

# Aguardar estabilização
echo "⏳ Aguardando servidores estabilizarem (10 segundos)..."
sleep 10
echo ""

# Verificar se está rodando
echo "📊 Verificando servidores..."
echo ""

if lsof -i :5001 | grep -q LISTEN; then
    echo "   ✅ Python Backend (5001) - ONLINE"
else
    echo "   ❌ Python Backend (5001) - OFFLINE"
    echo "      Verifique: tail -20 /tmp/python_backend.log"
fi

if lsof -i :3000 | grep -q LISTEN; then
    echo "   ✅ Frontend (3000) - ONLINE"
else
    echo "   ❌ Frontend (3000) - OFFLINE"
    echo "      Verifique: tail -20 /tmp/frontend.log"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Teste final
if lsof -i :3000 | grep -q LISTEN && lsof -i :5001 | grep -q LISTEN; then
    echo "✅✅✅ SISTEMA PRONTO! ✅✅✅"
    echo ""
    echo "🌐 ACESSE: http://localhost:3000"
    echo ""
    echo "📋 Código de Convite: X6OCSFJFA1Z8KT5"
    echo ""
else
    echo "⚠️ Algum servidor não iniciou corretamente"
    echo ""
    echo "Logs disponíveis em:"
    echo "   - Python: /tmp/python_backend.log"
    echo "   - Frontend: /tmp/frontend.log"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 DICAS:"
echo ""
echo "   • Ver logs Python: tail -f /tmp/python_backend.log"
echo "   • Ver logs Frontend: tail -f /tmp/frontend.log"
echo "   • Parar tudo: pkill -f uvicorn; pkill -f tsx"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

