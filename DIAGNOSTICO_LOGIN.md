# 🔍 Diagnóstico de Erro de Login Pós-Deploy

## ⚠️ PROBLEMA IDENTIFICADO

**Sistema deployado com sucesso**, mas login não funciona com credenciais.

---

## 🎯 CAUSAS MAIS PROVÁVEIS

### 1️⃣ **Banco de Dados Vazio** (MAIS PROVÁVEL)

O banco de dados em produção pode estar vazio (sem usuários cadastrados).

**Solução**: Criar usuário inicial via script de seed ou registro manual.

### 2️⃣ **Variáveis de Ambiente Incorretas**

- `DATABASE_URL` apontando para banco errado
- `SESSION_SECRET` não configurado
- `ANTHROPIC_API_KEY` faltando

### 3️⃣ **Backend Não Conectando ao Banco**

- Credenciais PostgreSQL incorretas
- Host/porta do banco incorretos no docker-compose

### 4️⃣ **Tabelas Não Criadas**

- Migrations não rodaram
- Schema não foi aplicado

---

## 🔧 SOLUÇÕES RÁPIDAS

### Opção A: Criar Usuário Admin via SQL

**No Dokploy**, acesse o terminal do container PostgreSQL e execute:

\`\`\`sql
-- Ver se tabela users existe
SELECT COUNT(*) FROM users;

-- Se existir mas estiver vazia, criar usuário admin:
INSERT INTO users (id, username, email, password, role, created_at)
VALUES (
    gen_random_uuid(),
    'admin',
    'seu-email@exemplo.com',
    -- Senha: 'admin123' (bcrypt hash)
    '$2b$10$rQvYJF.xJKPLXLLxKJZVNuK8YdLl7y8VvYhKZgXHQR8QhT3PqKqSK',
    'superadmin',
    NOW()
);
\`\`\`

**Depois faça login com:**
- Email: `seu-email@exemplo.com`
- Senha: `admin123`

### Opção B: Verificar Logs do Backend

No Dokploy, veja os logs do container `advisory-app`:

\`\`\`bash
# Procure por erros como:
# - "Connection refused"
# - "Table does not exist"
# - "Authentication failed"
\`\`\`

### Opção C: Executar Script de Seed

Se o backend estiver rodando, acesse o terminal do container:

\`\`\`bash
docker exec -it advisory-app bash
cd python_backend
python -c "
import asyncio
from storage import MemStorage
from seed import seed_legends

async def main():
    storage = MemStorage()
    await seed_legends(storage)
    print('✅ Legends seeded!')

asyncio.run(main())
"
\`\`\`

---

## 📋 CHECKLIST DE DIAGNÓSTICO

Execute em ordem:

1. **[ ] Verificar se containers estão rodando**
   - No Dokploy: Ver status de `advisory-app` e `advisory-postgres`
   
2. **[ ] Ver logs do backend**
   - Procurar por erros de conexão com banco
   
3. **[ ] Conectar no banco e verificar tabelas**
   \`\`\`sql
   \dt  -- listar todas as tabelas
   SELECT COUNT(*) FROM users;
   \`\`\`
   
4. **[ ] Verificar variáveis de ambiente**
   - No Dokploy: Confirmar `DATABASE_URL`, `SESSION_SECRET`, `ANTHROPIC_API_KEY`
   
5. **[ ] Testar endpoint de health**
   \`\`\`bash
   curl http://SUA-URL:5002/api/health
   \`\`\`

---

## 🚨 ERRO ESPECÍFICO QUE VOCÊ VÊ

**Por favor, me informe:**

1. **Mensagem de erro exata** que aparece na tela
2. **Console do navegador (F12)** - algum erro em vermelho?
3. **Logs do Dokploy** - últimas 20 linhas do container `advisory-app`

Com essas informações posso dar a solução exata! 🎯

