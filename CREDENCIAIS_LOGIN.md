# 🔑 Credenciais de Login - Advisory Replit

**Data:** 10 de novembro de 2025, 02:30  
**Status:** ✅ Códigos Válidos

---

## 🆕 NOVO CÓDIGO DE CONVITE GERADO:

```
O9L2R6XW5AVHTAE
```

**Use para:** Criar uma NOVA conta  
**URL:** http://localhost:3000/register

---

## 👥 CONTAS EXISTENTES:

Você já tem **4 contas** cadastradas! Pode fazer login com qualquer uma:

### 1. gabriel@teste.com
- **Usuario:** gabriel
- **Email:** gabriel@teste.com
- **Senha:** (a que você criou)

### 2. debug@teste.com
- **Usuario:** teste_debug
- **Email:** debug@teste.com
- **Senha:** (a que você criou)

### 3. teste_final@exemplo.com
- **Usuario:** teste_final
- **Email:** teste_final@exemplo.com
- **Senha:** (a que você criou)

### 4. novo@teste.com
- **Usuario:** usuario_novo
- **Email:** novo@teste.com
- **Senha:** (a que você criou)

---

## 🎯 COMO FAZER LOGIN:

### Opção 1: Usar Conta Existente

1. **Abra:** http://localhost:3000/login

2. **Preencha:**
   - Email: (um dos acima)
   - Senha: (a que você criou)

3. **Click:** "Entrar"

4. ✅ **PRONTO!** Você está logado!

### Opção 2: Criar Nova Conta

1. **Abra:** http://localhost:3000/register

2. **Preencha:**
   - Nome: Seu nome
   - Email: seu@email.com
   - Senha: (crie uma senha)
   - **Código:** `O9L2R6XW5AVHTAE`

3. **Click:** "Registrar"

4. ✅ **PRONTO!** Conta criada e logado!

---

## 🔒 SE ESQUECEU A SENHA:

**Opção 1: Criar Nova Conta**
- Use o código: `O9L2R6XW5AVHTAE`
- Crie com novo email

**Opção 2: Resetar Senha no Banco** (Avançado)
```bash
# Via terminal - alterar senha de uma conta
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import asyncio
import asyncpg
import os
import bcrypt
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))

async def reset_password():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Alterar senha do gabriel@teste.com para "senha123"
        nova_senha = "senha123"
        hash_senha = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
        
        await conn.execute("""
            UPDATE users 
            SET password = $1
            WHERE email = $2
        """, hash_senha, 'gabriel@teste.com')
        
        print(f"✅ Senha alterada!")
        print(f"   Email: gabriel@teste.com")
        print(f"   Nova senha: senha123")
        
    finally:
        await conn.close()

asyncio.run(reset_password())
EOF
```

---

## 📋 TODOS OS CÓDIGOS DISPONÍVEIS:

### Código NOVO (Gerado Agora):
```
O9L2R6XW5AVHTAE
```

### Código ANTIGO (Ainda Válido):
```
X6OCSFJFA1Z8KT5
```

**Ambos funcionam!** Use qualquer um para criar conta.

---

## 🎯 RECOMENDAÇÃO:

### **Opção Mais Simples:**

**Se você lembra da senha de alguma conta:**
1. Vá em http://localhost:3000/login
2. Use gabriel@teste.com (ou outro email)
3. Digite a senha
4. ✅ Login!

**Se NÃO lembra de nenhuma senha:**
1. Vá em http://localhost:3000/register
2. Crie nova conta
3. Use código: `O9L2R6XW5AVHTAE`
4. ✅ Conta nova!

---

## ✅ APÓS LOGIN:

Quando você estiver logado, você verá:

```
┌──────────────────────────────────────────┐
│  🏠 Home    [seu nome] ▼                 │
├──────────────────────────────────────────┤
│                                          │
│  Menu:                                   │
│  • Home                                  │
│  • Categorias                            │
│  • Conversas                             │
│  • Conselho Estratégico                  │
│  • Persona Builder  ← AQUI!              │
│  • Analytics                             │
│                                          │
└──────────────────────────────────────────┘
```

**Click em "Persona Builder"** para ver/criar personas!

---

## 🎊 RESUMO:

**Você tem 2 opções:**

### Opção A: Login com Conta Existente ⚡ (Mais Rápido)
- Email: `gabriel@teste.com` (ou qualquer outro acima)
- Senha: (a que você criou)
- URL: http://localhost:3000/login

### Opção B: Criar Nova Conta 🆕
- Código: `O9L2R6XW5AVHTAE`
- URL: http://localhost:3000/register

---

**🚀 AMBAS OPÇÕES FUNCIONAM!**

**Escolha uma e acesse o sistema agora!** 😊

