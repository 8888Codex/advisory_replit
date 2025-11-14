# 🚨 URGENTE: Container Não Está Rodando

## ❌ Problema

**Erro:** `container is not running`  
**Sintoma:** `ERR_CONNECTION_REFUSED` ao acessar `http://72.60.244.72:3001`

**Causa:** O container foi criado mas crashou ao iniciar (provavelmente por variáveis de ambiente faltando).

---

## 🔍 AÇÃO IMEDIATA: Verificar Logs

**No Dokploy:**

1. Vá na aplicação "O Conselho"
2. Clique na aba **"Logs"**
3. **Veja TODOS os logs desde o início** (não apenas as últimas linhas)
4. Procure por mensagens de erro que começam com `❌ ERROR:`

---

## 🎯 ERROS MAIS COMUNS

### Erro 1: Variáveis de Ambiente Faltando

**Se aparecer nos logs:**
```
❌ ERROR: DATABASE_URL não configurado
```
ou
```
❌ ERROR: ANTHROPIC_API_KEY não configurado
```
ou
```
❌ ERROR: SESSION_SECRET não configurado
```

**Solução:**

1. No Dokploy, vá em **Environment**
2. Adicione estas variáveis **OBRIGATÓRIAS**:

```bash
DATABASE_URL=postgresql://user:password@host:port/database
ANTHROPIC_API_KEY=sk-ant-api03-sua-chave-aqui
SESSION_SECRET=seu-secret-minimo-32-caracteres-aqui
NODE_ENV=production
```

3. **Salve**
4. Clique em **"Restart"** (não rebuild, apenas restart)

---

### Erro 2: Arquivo Não Encontrado

**Se aparecer nos logs:**
```
❌ ERROR: dist/index.js não encontrado! O build falhou?
```

**Solução:**
- O build pode ter falhado
- Faça rebuild completo no Dokploy

---

### Erro 3: Dependências Python

**Se aparecer nos logs:**
```
❌ ERROR: Uvicorn não está instalado!
```

**Solução:**
- Problema no build do Python
- Faça rebuild completo

---

## 📋 CHECKLIST RÁPIDO

1. **Veja os logs completos** - qual erro aparece primeiro?
2. **Verifique Environment** - todas as variáveis obrigatórias estão configuradas?
3. **Tente restart** - após configurar variáveis, faça restart
4. **Se não funcionar** - faça rebuild completo

---

## 🆘 PRÓXIMOS PASSOS

**Envie-me:**

1. **Primeiras 20-30 linhas dos logs** (onde aparece o erro)
2. **Screenshot da aba Environment** (sem mostrar valores sensíveis)
3. **Qual erro específico aparece?**

Com essas informações, identifico o problema exato e forneço a solução! 🔍

---

## 💡 DICA

**90% dos casos de container não rodar é por variáveis de ambiente faltando!**

Verifique primeiro a aba **Environment** no Dokploy e certifique-se de que TODAS as variáveis obrigatórias estão configuradas.

