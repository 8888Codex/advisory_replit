# Arquitetura: Vite em Produção vs Desenvolvimento

## ✅ Solução Implementada

Esta solução garante que **Vite NÃO é necessário em runtime de produção**. O servidor Node em produção serve apenas arquivos estáticos pré-compilados.

---

## 📋 Arquivos Modificados

### 1. `package.json`
- **Removido** `vite` e plugins do vite de `dependencies`
- **Movido** `vite` e plugins para `devDependencies`
- **Modificado** script `build` para usar dois passos:
  - `build:client` - Compila frontend com Vite
  - `build:server` - Compila servidor Node com esbuild (sem Vite)

### 2. `esbuild.config.mjs` (NOVO)
- Configuração do esbuild para produção
- Plugin que marca `vite.ts` e `vite.config.ts` como externos
- Tree-shaking e minificação ativados para remover código morto
- Garante que código relacionado ao Vite não seja incluído no bundle

### 3. `server/index.ts`
- Verificação robusta de ambiente: `process.env.NODE_ENV !== 'production'`
- Import dinâmico do Vite apenas em desenvolvimento
- Try/catch para fallback seguro se Vite não estiver disponível
- Em produção, sempre usa `serveStatic()`

### 4. `Dockerfile`
- Remove `server/vite.ts` após copiar arquivos do servidor
- Garante que arquivo de desenvolvimento não seja incluído no container

---

## 🔄 Fluxo de Build e Execução

### **DESENVOLVIMENTO**

```bash
# Inicia servidor com Vite dev server
npm run dev
```

**O que acontece:**
1. `tsx server/index.ts` executa diretamente (sem build)
2. `NODE_ENV=development` → código importa `./vite` dinamicamente
3. Vite dev server é iniciado e serve frontend com HMR
4. Backend Node serve API + Vite middleware

---

### **PRODUÇÃO - Build**

```bash
# Build completo (client + server)
npm run build
```

**O que acontece:**

1. **`build:client`** (`vite build`):
   - Compila frontend React/TypeScript
   - Gera arquivos estáticos em `dist/public/`
   - **Vite NÃO é necessário após este passo**

2. **`build:server`** (`node esbuild.config.mjs`):
   - Compila `server/index.ts` com esbuild
   - **Exclui** `server/vite.ts` do bundle
   - **Exclui** imports de `vite` e plugins
   - Tree-shaking remove código morto (`if (false)`)
   - Gera `dist/index.js` **SEM dependências de Vite**

---

### **PRODUÇÃO - Execução**

```bash
# Inicia servidor em produção
npm start
# ou
NODE_ENV=production node dist/index.js
```

**O que acontece:**
1. `NODE_ENV=production` → `isDevelopment = false`
2. Código relacionado ao Vite foi removido pelo tree-shaking
3. Servidor usa apenas `serveStatic()` para servir `dist/public/`
4. **Nenhum import de Vite é executado**
5. **Vite não é necessário em runtime**

---

## 🐳 Docker

### Build Stage
```dockerfile
# Stage 1: Build Frontend
RUN npm ci  # Instala TODAS as dependências (incluindo devDependencies)
RUN npm run build  # Executa build:client + build:server
```

### Runtime Stage
```dockerfile
# Instala APENAS dependências de produção
RUN npm ci --only=production  # Vite NÃO é instalado aqui

# Remove vite.ts do container
RUN rm -f ./server/vite.ts
```

**Resultado:** Container de produção não tem Vite instalado e não precisa dele.

---

## ✅ Verificações

### Verificar que Vite não está no bundle:
```bash
# Não deve encontrar imports de vite
grep -i "import.*vite\|from.*vite" dist/index.js
# Resultado esperado: nenhuma linha encontrada
```

### Verificar que código de desenvolvimento foi removido:
```bash
# Não deve encontrar referências ao código de desenvolvimento
grep -i "isDevelopment\|viteModule\|setupVite" dist/index.js
# Resultado esperado: nenhuma linha encontrada
```

### Testar build localmente:
```bash
# 1. Build
npm run build

# 2. Verificar que dist/index.js existe
ls -lh dist/index.js

# 3. Testar em produção (sem Vite instalado)
NODE_ENV=production node dist/index.js
```

---

## 🎯 Benefícios

1. **✅ Arquitetura Correta**: Vite é ferramenta de build, não runtime dependency
2. **✅ Bundle Menor**: Código relacionado ao Vite não está no bundle de produção
3. **✅ Sem Dependências Desnecessárias**: Vite não precisa estar instalado em produção
4. **✅ Performance**: Servidor de produção serve apenas arquivos estáticos pré-compilados
5. **✅ Segurança**: Menos dependências = menor superfície de ataque

---

## 📝 Notas Técnicas

- O esbuild usa tree-shaking para remover código morto (`if (false)`)
- O plugin `exclude-vite-files` marca arquivos relacionados ao Vite como externos
- O Dockerfile remove `server/vite.ts` para garantir que não seja copiado
- O código usa verificação dupla: `process.env.NODE_ENV` + `app.get("env")`

---

## 🚀 Próximos Passos

1. Testar build localmente: `npm run build && npm start`
2. Testar no Docker: `docker build -t test-app . && docker run -p 3001:3001 test-app`
3. Verificar logs para confirmar que não há erros relacionados ao Vite
4. Fazer deploy e verificar que aplicação funciona corretamente

