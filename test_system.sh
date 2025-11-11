#!/bin/bash
set -e

echo "🧪 TESTANDO SISTEMA ADVISORY REPLIT"
echo "===================================="
echo ""

# Test 1: Environment variables
echo "✓ Teste 1: Variáveis de Ambiente"
if [ -f .env ]; then
    echo "  ✅ Arquivo .env existe"
    if grep -q "DATABASE_URL" .env && grep -q "ANTHROPIC_API_KEY" .env; then
        echo "  ✅ Variáveis principais configuradas"
    else
        echo "  ❌ Variáveis faltando no .env"
        exit 1
    fi
else
    echo "  ❌ Arquivo .env não encontrado"
    exit 1
fi
echo ""

# Test 2: Node dependencies
echo "✓ Teste 2: Dependências Node.js"
if [ -d node_modules ]; then
    echo "  ✅ node_modules existe ($(ls node_modules | wc -l | tr -d ' ') pacotes)"
else
    echo "  ❌ node_modules não encontrado"
    exit 1
fi
echo ""

# Test 3: Python environment
echo "✓ Teste 3: Ambiente Python"
if [ -d .venv ]; then
    echo "  ✅ .venv existe"
    export PATH="$HOME/.local/bin:$PATH"
    source .venv/bin/activate
    echo "  ✅ Virtual environment ativado"
else
    echo "  ❌ .venv não encontrado"
    exit 1
fi
echo ""

# Test 4: Database connection
echo "✓ Teste 4: Conexão com Banco de Dados"
python3 -c "
import asyncpg, asyncio, os
from dotenv import load_dotenv
load_dotenv()
async def test():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        result = await conn.fetchval('SELECT COUNT(*) FROM users')
        await conn.close()
        print(f'  ✅ Conectado ao banco Neon ({result} usuários)')
        return True
    except Exception as e:
        print(f'  ❌ Erro: {e}')
        return False
asyncio.run(test())
" || exit 1
echo ""

# Test 5: Python Backend (quick start/stop)
echo "✓ Teste 5: Python Backend"
cd python_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 5001 > /tmp/test_python.log 2>&1 &
PYTHON_PID=$!
cd ..
sleep 6

if curl -s http://localhost:5001/ > /dev/null 2>&1; then
    RESPONSE=$(curl -s http://localhost:5001/)
    echo "  ✅ Python Backend funcionando: $RESPONSE"
    
    # Teste endpoint de experts
    EXPERTS_COUNT=$(curl -s http://localhost:5001/api/experts | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "  ✅ API experts carregados: $EXPERTS_COUNT experts"
else
    echo "  ❌ Python Backend não respondeu"
    cat /tmp/test_python.log | tail -20
    kill $PYTHON_PID 2>/dev/null
    exit 1
fi
kill $PYTHON_PID 2>/dev/null
sleep 2
echo ""

# Test 6: Node.js Server
echo "✓ Teste 6: Node.js Server + Frontend"
npm run dev > /tmp/test_node.log 2>&1 &
NODE_PID=$!
sleep 10

if curl -s http://localhost:5000/ > /dev/null 2>&1; then
    HTML_SIZE=$(curl -s http://localhost:5000/ | wc -c | tr -d ' ')
    echo "  ✅ Node.js Server funcionando (HTML: ${HTML_SIZE} bytes)"
else
    echo "  ❌ Node.js Server não respondeu"
    cat /tmp/test_node.log | tail -20
    kill $NODE_PID 2>/dev/null
    exit 1
fi
kill $NODE_PID 2>/dev/null
sleep 2
echo ""

echo "=================================="
echo "✅ TODOS OS TESTES PASSARAM!"
echo "=================================="
echo ""
echo "📝 Comandos para rodar o sistema:"
echo "   ./start_all.sh          # Inicia ambos servidores"
echo "   npm run dev             # Apenas frontend (porta 5000)"
echo "   cd python_backend && uvicorn main:app --reload  # Apenas backend Python"
echo ""

