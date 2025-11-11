# 🎉 Sistema Funcionando! Como Usar

## ✅ Status Atual

**SISTEMA 100% OPERACIONAL!**

- ✅ Python Backend: http://localhost:5001
- ✅ Frontend React: http://localhost:3000
- ✅ Banco de Dados Neon: Conectado
- ✅ 18 Experts: Carregados e prontos

---

## 🌐 ACESSE AGORA

**Abra seu navegador e vá para:**

```
http://localhost:3000
```

---

## 🎯 O que Você Pode Fazer

### 1. **Criar Conta**
- Registre-se na plataforma
- Complete o onboarding

### 2. **Explorar Experts** (18 disponíveis)
- Philip Kotler (Marketing Strategy)
- Seth Godin (Marketing)
- David Ogilvy (Advertising)
- Gary Vaynerchuk (Social Media)
- Simon Sinek (Leadership)
- Neil Patel (SEO/Growth)
- Eugene Schwartz (Copywriting)
- Claude Hopkins (Direct Response)
- E mais 10 experts!

### 3. **Conversar com Experts**
- Escolha um expert
- Faça perguntas sobre marketing
- Receba conselhos personalizados

### 4. **Council Room**
- Reúna múltiplos experts
- Debate entre diferentes perspectivas
- Análise profunda de problemas

---

## 🛑 Para Parar os Servidores

```bash
pkill -f "uvicorn"
pkill -f "tsx"
```

---

## 🚀 Para Iniciar Novamente

**Terminal 1 - Python Backend:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
cd python_backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 5001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
npm run dev
```

**OU use o script automático:**
```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
./start_all.sh
```

---

## 📁 Estrutura do Projeto

```
advisory_replit/
├── client/              # Frontend React
├── server/              # Backend Node.js (Express)
├── python_backend/      # Backend Python (FastAPI + IA)
│   ├── clones/         # 18 experts
│   └── tools/          # Perplexity, YouTube, etc.
├── .env                # Suas configurações (NUNCA commitar!)
└── package.json
```

---

## 🔧 Desenvolvimento

### Para Modificar o Frontend:
- Edite arquivos em `client/src/`
- O Vite recarrega automaticamente

### Para Modificar os Experts:
- Edite arquivos em `python_backend/clones/`
- O Uvicorn recarrega automaticamente

### Para Adicionar Novos Experts:
- Crie novo arquivo em `python_backend/clones/`
- Siga o padrão dos existentes
- Registre no `registry.py`

---

## 🐛 Problemas Comuns

**Erro "porta ocupada":**
```bash
pkill -f "uvicorn"
pkill -f "tsx"
```

**Erro "DATABASE_URL not found":**
- Verifique se o arquivo `.env` existe
- Verifique se tem a variável `DATABASE_URL`

**Frontend não carrega:**
- Verifique se Python backend está rodando primeiro
- Acesse http://localhost:5001 para testar

---

## 📞 APIs Disponíveis

### Python Backend (porta 5001):
- `GET /` - Health check
- `GET /api/experts` - Lista todos os experts
- `POST /api/conversations` - Criar conversa
- `POST /api/conversations/:id/messages` - Enviar mensagem
- E muitas outras...

### Documentação Automática:
```
http://localhost:5001/docs
```

---

## 🎓 Próximos Passos

1. **Explore a interface**
2. **Converse com os experts**
3. **Veja o código para entender**
4. **Adicione suas melhorias**
5. **Faça deploy quando pronto**

---

## 💡 Dicas

- **Ctrl+C** para parar um servidor
- Use **dois terminais** (um para cada servidor)
- Logs aparecem em tempo real
- Erros são mostrados no terminal

---

**Criado em**: 9 de novembro de 2025
**Status**: ✅ Funcionando perfeitamente!

Divirta-se desenvolvendo! 🚀

