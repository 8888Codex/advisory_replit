# 🌐 Como Acessar a Aplicação em Produção (Dokploy)

**Status:** ✅ Deploy realizado com sucesso!

---

## 🎯 URLS DE ACESSO

### Opção 1: Via IP e Porta (Direto)

A aplicação está rodando na **porta 3001**:

```
http://72.60.244.72:3001
```

**Ou:**

```
http://72.60.244.72:3001/
```

---

### Opção 2: Via Domínio (Se Configurado)

Se você configurou um domínio no Dokploy:

1. Acesse o Dokploy: `http://72.60.244.72:3000/dashboard/projects`
2. Vá na sua aplicação
3. Clique na aba **"Domains"** ou **"Settings"**
4. Veja se há um domínio configurado

Se houver domínio configurado, acesse:
```
https://seu-dominio.com
```

---

## 🔍 COMO VERIFICAR A URL CORRETA NO DOKPLOY

### Passo 1: Acessar o Dashboard do Dokploy

```
http://72.60.244.72:3000/dashboard/projects
```

### Passo 2: Selecionar sua Aplicação

- Clique no projeto **"o-conselho"** (ou o nome que você deu)

### Passo 3: Verificar a URL de Acesso

Procure por uma das seguintes opções:

1. **Aba "Overview" ou "Details"**
   - Deve mostrar a URL de acesso
   - Exemplo: `http://72.60.244.72:3001` ou `https://o-conselho.seudominio.com`

2. **Aba "Domains"**
   - Lista todos os domínios configurados
   - Se houver domínio, use ele

3. **Aba "Settings" > "Ports"**
   - Mostra a porta exposta (deve ser 3001)
   - A URL será: `http://SEU-IP:3001`

---

## ✅ TESTE RÁPIDO DE ACESSO

### Teste 1: Health Check

Abra seu navegador ou terminal e teste:

```bash
curl http://72.60.244.72:3001/api/health
```

**Esperado:**
```json
{
  "status": "ok",
  "node": "healthy",
  "python": "healthy",
  "timestamp": "2024-..."
}
```

### Teste 2: Acessar no Navegador

1. Abra seu navegador (Chrome, Firefox, Safari, etc.)
2. Digite na barra de endereço:
   ```
   http://72.60.244.72:3001
   ```
3. Pressione Enter

**Você deve ver:**
- A tela de login ou registro da aplicação
- Ou a página inicial do sistema

---

## 🔑 PRIMEIRO ACESSO

### Se o banco de dados está vazio:

Você precisa criar um usuário inicial. Opções:

#### Opção A: Criar via SQL (Recomendado)

1. Acesse o terminal do PostgreSQL no Dokploy
2. Execute o script `criar_usuario_producao.sql`

**Credenciais padrão:**
- Email: `admin@oconselho.com` (troque pelo seu email)
- Senha: `admin123`

⚠️ **IMPORTANTE:** Mude a senha após o primeiro login!

#### Opção B: Registrar pela Interface

1. Acesse `http://72.60.244.72:3001/register`
2. Preencha o formulário de registro
3. Use um código de convite (se necessário)

---

## 🆘 SE NÃO CONSEGUIR ACESSAR

### Problema 1: Página não carrega

**Verificar:**

1. **A aplicação está rodando?**
   - No Dokploy, vá em "Logs"
   - Procure por: `serving on port 3001`
   - Se não aparecer, a aplicação pode não ter iniciado

2. **A porta está exposta?**
   - No Dokploy: Settings > Ports
   - Deve ter a porta 3001 exposta
   - Se não tiver, adicione manualmente

3. **Firewall bloqueando?**
   - Verifique se o firewall do servidor permite conexões na porta 3001
   - No Dokploy, verifique as configurações de rede

### Problema 2: Erro 401 ou 500

**Verificar:**

1. **Python backend está rodando?**
   ```bash
   curl http://72.60.244.72:5002/api/health
   ```
   Deve retornar: `{"status": "healthy"}`

2. **Variáveis de ambiente configuradas?**
   - No Dokploy: Settings > Environment
   - Verifique se `DATABASE_URL`, `ANTHROPIC_API_KEY`, `SESSION_SECRET` estão configuradas

### Problema 3: Erro de CORS

Se aparecer erro de CORS no console do navegador:

1. No Dokploy, adicione a variável de ambiente:
   ```
   ALLOWED_ORIGINS=http://72.60.244.72:3001,https://seu-dominio.com
   ```
2. Faça rebuild da aplicação

---

## 📊 VERIFICAÇÃO COMPLETA

Execute estes testes para confirmar que tudo está funcionando:

### 1. Health Check do Node
```bash
curl http://72.60.244.72:3001/api/health
```

### 2. Health Check do Python
```bash
curl http://72.60.244.72:5002/api/health
```

### 3. Acessar no Navegador
```
http://72.60.244.72:3001
```

### 4. Verificar Logs no Dokploy
- Vá em "Logs" da aplicação
- Procure por mensagens de erro
- Deve aparecer: `serving on port 3001`

---

## 🎯 URLS IMPORTANTES

| Recurso | URL |
|---------|-----|
| **Aplicação Principal** | `http://72.60.244.72:3001` |
| **Health Check Node** | `http://72.60.244.72:3001/api/health` |
| **Health Check Python** | `http://72.60.244.72:5002/api/health` |
| **Dashboard Dokploy** | `http://72.60.244.72:3000/dashboard/projects` |
| **Login** | `http://72.60.244.72:3001/login` |
| **Registro** | `http://72.60.244.72:3001/register` |

---

## 💡 DICA: Configurar Domínio Personalizado

Para usar um domínio personalizado (ex: `o-conselho.seudominio.com`):

1. No Dokploy, vá em Settings > Domains
2. Adicione seu domínio
3. Configure o DNS apontando para `72.60.244.72`
4. Dokploy configurará SSL automaticamente (Let's Encrypt)
5. Aguarde alguns minutos para o certificado ser emitido
6. Acesse via `https://seu-dominio.com`

---

## ✅ CHECKLIST DE ACESSO

- [ ] Health check do Node responde (`/api/health`)
- [ ] Health check do Python responde (`/api/health` na porta 5002)
- [ ] Aplicação carrega no navegador (`http://72.60.244.72:3001`)
- [ ] Tela de login/registro aparece
- [ ] Usuário inicial criado (se necessário)
- [ ] Login funciona sem erro 401
- [ ] Console do navegador sem erros (F12)

---

**Se ainda tiver problemas, me avise qual erro aparece!** 🚀

