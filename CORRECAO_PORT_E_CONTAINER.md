# 🔧 Correção: PORT=3000 e Container Não Encontrado

## ❌ Problemas Identificados

### Problema 1: PORT Configurado Incorretamente
**Variável de ambiente:** `PORT=3000`  
**Deveria ser:** `PORT=3001`

**Impacto:** A aplicação pode estar tentando rodar na porta errada.

---

### Problema 2: Container Não Encontrado
**Erro:** `No such container: 547ecf59ee8f`

**Causa:** O Dokploy está tentando acessar um container antigo que foi removido após o rebuild.

---

## ✅ SOLUÇÕES

### Solução 1: Corrigir Variável PORT

**No Dokploy:**

1. Vá na aba **"Environment"**
2. Procure pela variável `PORT`
3. **Altere de `3000` para `3001`**
4. Salve
5. Faça **Restart** da aplicação (não rebuild)

**OU remova a variável PORT completamente** - o `start.sh` já define `PORT=3001` automaticamente.

---

### Solução 2: Verificar se Container Está Rodando

**No Dokploy, aba "Terminal" ou "Shell":**

Execute:
```bash
# Ver todos os containers
docker ps -a

# Ver containers rodando
docker ps

# Ver containers da aplicação
docker ps -a | grep o-conselho
```

**Se não aparecer nenhum container:**
- O Dokploy não iniciou o container após o build
- Tente fazer **Restart** manualmente

---

### Solução 3: Iniciar Container Manualmente (se necessário)

**No Dokploy:**

1. Vá na aplicação
2. Clique em **"Restart"** ou **"Start"**
3. Aguarde alguns segundos
4. Verifique os logs novamente

---

### Solução 4: Verificar Logs de Execução

**No Dokploy:**

1. Vá na aba **"Logs"**
2. **Procure por logs APÓS o build** (não apenas os logs de build)
3. Se não aparecer nada após "Docker Deployed: ✅":
   - O container não foi iniciado automaticamente
   - Faça restart manual

---

## 📋 CHECKLIST

- [ ] **Variável PORT corrigida?**
  - Deve ser `3001` ou removida (start.sh define automaticamente)
  
- [ ] **Container está rodando?**
  - `docker ps` mostra container com status `Up`
  
- [ ] **Logs mostram aplicação iniciando?**
  - Procure por "serving on port 3001 (host: 0.0.0.0)"
  
- [ ] **Restart foi feito após corrigir PORT?**
  - Não rebuild, apenas restart

---

## 🆘 PRÓXIMOS PASSOS

1. **Corrija a variável PORT** de `3000` para `3001` (ou remova)
2. **Faça Restart** da aplicação
3. **Aguarde 30-60 segundos**
4. **Verifique os logs novamente** - deve aparecer logs de execução
5. **Teste o health check:** `curl http://localhost:3001/api/health`

---

## 💡 DICA

**A variável PORT no Dokploy pode estar sobrescrevendo o PORT=3001 do start.sh!**

**Solução:** Remova a variável `PORT` do Environment completamente. O `start.sh` já define `PORT=3001` automaticamente.

---

**Após corrigir, me envie os novos logs!** 📋

