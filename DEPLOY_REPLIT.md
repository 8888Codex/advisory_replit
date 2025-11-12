# 🚀 Deploy no Replit - Guia Completo

## ✅ Configuração Pronta

O projeto está configurado para deploy no Replit com:
- ✅ Script de inicialização (`start_replit.sh`)
- ✅ Configuração do Replit (`.replit`)
- ✅ Build automático
- ✅ Inicialização de Python + Node

---

## 📋 Passo a Passo

### 1. Importar Projeto no Replit

1. Acesse [replit.com](https://replit.com)
2. Clique em **"Create Repl"**
3. Selecione **"Import from GitHub"**
4. Cole a URL do repositório: `https://github.com/8888Codex/advisory_replit.git`
5. Clique em **"Import"**

---

### 2. Configurar Variáveis de Ambiente

No Replit, vá em **"Secrets"** (ícone de cadeado) e adicione:

#### Obrigatórias:
```
DATABASE_URL=postgresql://user:password@host:port/database
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SESSION_SECRET=seu-secret-aqui-minimo-32-caracteres
NODE_ENV=production
```

#### Opcionais (mas recomendadas):
```
PERPLEXITY_API_KEY=your-perplexity-key
YOUTUBE_API_KEY=your-youtube-key
GEMINI_API_KEY=your-gemini-key
REDIS_URL=redis://host:port
REDIS_ENABLED=true
```

**Importante:** 
- Use **"Secrets"** para variáveis sensíveis (não `.env`)
- O Replit injeta secrets automaticamente como variáveis de ambiente

---

### 3. Instalar Dependências Python

No Shell do Replit, execute:

```bash
# Instalar dependências Python
pip install -r <(python3 -c "import tomli; print('\n'.join(tomli.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" 2>/dev/null || echo "uvicorn fastapi anthropic asyncpg bcrypt crewai crewai-tools google-generativeai httpx loguru pillow pydantic python-dotenv redis requests resend tenacity youtube-transcript-api")
```

**OU** instale manualmente:

```bash
pip install uvicorn fastapi anthropic asyncpg bcrypt crewai crewai-tools google-generativeai httpx loguru pillow pydantic python-dotenv redis requests resend tenacity youtube-transcript-api
```

---

### 4. Fazer Build

No Shell do Replit, execute:

```bash
npm install
npm run build
```

**OU** simplesmente clique em **"Run"** - o Replit fará build automaticamente antes de iniciar.

---

### 5. Iniciar Aplicação

Clique no botão **"Run"** no Replit.

O script `start_replit.sh` irá:
1. ✅ Verificar variáveis de ambiente
2. ✅ Criar diretórios necessários
3. ✅ Iniciar Python backend (porta 5002)
4. ✅ Aguardar Python estar pronto
5. ✅ Iniciar Node server (porta do Replit)

---

## 🔍 Verificar se Está Funcionando

### Logs Esperados:

```
🚀 Iniciando O Conselho Marketing Advisory Platform (Replit)
==================================================
✅ Todas as variáveis obrigatórias configuradas
✅ Diretórios criados
✅ Dependências Python OK
🐍 Iniciando Python backend (porta 5002)...
⏳ Aguardando Python backend inicializar...
✅ Python backend pronto! (PID: XXXX)
🟢 Iniciando Node server (porta 5000)...
==================================================
serving on port 5000 (host: 0.0.0.0)
```

### Testar Health Check:

No Shell do Replit:
```bash
curl http://localhost:5000/api/health
```

Deve retornar:
```json
{
  "status": "ok",
  "node": "healthy",
  "python": "healthy",
  "timestamp": "2024-..."
}
```

---

## 🌐 Acessar Aplicação

Após iniciar, o Replit mostrará uma URL como:
```
https://o-conselho-seu-usuario.replit.app
```

Clique na URL para acessar a aplicação.

---

## 🔧 Troubleshooting

### Problema: Python não inicia

**Solução:**
```bash
# Verificar se uvicorn está instalado
python3 -c "import uvicorn"

# Se não estiver, instalar
pip install uvicorn fastapi
```

---

### Problema: Build falha

**Solução:**
```bash
# Limpar e reinstalar
rm -rf node_modules dist
npm install
npm run build
```

---

### Problema: Porta já em uso

**Solução:**
- O Replit gerencia portas automaticamente
- Use a variável `PORT` que o Replit fornece
- Não defina PORT manualmente

---

### Problema: Variáveis de ambiente não funcionam

**Solução:**
- Use **"Secrets"** no Replit (não `.env`)
- Reinicie o Repl após adicionar secrets
- Verifique se os nomes estão corretos

---

## 📊 Monitoramento

### Ver Logs:

- **Python Backend:** `logs/python_backend.log`
- **Node Server:** Console do Replit

### Ver Processos:

```bash
# Ver processos Python
ps aux | grep uvicorn

# Ver processos Node
ps aux | grep node
```

---

## 🚀 Deploy Público (Always On)

Para manter a aplicação sempre rodando:

1. No Replit, vá em **"Deploy"**
2. Ative **"Always On"** (requer Replit Hacker plan)
3. Configure domínio customizado (opcional)

---

## 💡 Dicas

1. **Performance:** O Replit pode ser mais lento que servidores dedicados
2. **Limites:** Plano gratuito tem limites de recursos
3. **Backup:** Configure backup do banco de dados externo
4. **Logs:** Monitore logs regularmente para detectar problemas

---

## ✅ Checklist Final

- [ ] Projeto importado no Replit
- [ ] Variáveis de ambiente configuradas (Secrets)
- [ ] Dependências Python instaladas
- [ ] Build concluído (`npm run build`)
- [ ] Aplicação iniciando corretamente
- [ ] Health check funcionando
- [ ] URL pública acessível

---

**Pronto para deploy!** 🎉

