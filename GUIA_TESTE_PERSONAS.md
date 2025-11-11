# 🧪 Guia de Teste - Sistema de Personas

**Data:** 10 de novembro de 2025, 04:10  
**Status:** ✅ Criação OK | ⏳ Enrichment investigando

---

## ✅ STATUS ATUAL:

### **Funcionando:**
- ✅ Backend Python (5001)
- ✅ Frontend Node (3000)
- ✅ Criar persona com user_id correto
- ✅ Ver persona no dashboard
- ✅ Listar personas
- ✅ Deletar personas

### **Em investigação:**
- ⏳ Enrichment background task (fica em 'pending')

---

## 🎯 TESTE 1: VER SUA PERSONA ATUAL

### **URL:**
```
http://localhost:3000/persona-dashboard
```

### **O que você DEVE ver:**

```
┌──────────────────────────────────────────────┐
│  🧠 Persona Intelligence Hub                 │
├──────────────────────────────────────────────┤
│  📊 Cognita AI - Gabriel Lima                │
│  Indústria: Inteligência Artificial         │
│  Status: Pending (ou Processing/Completed)   │
└──────────────────────────────────────────────┘
```

---

## 🎯 TESTE 2: CRIAR NOVA PERSONA

### **Opção A: Via Interface** (Recomendado)

**URL:**
```
http://localhost:3000/personas
```

**Passos:**
1. Click em "Criar Nova Persona" (ou similar)
2. Preencha formulário
3. Salve

### **Opção B: Via API Direta** (Debug)

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import requests

your_user_id = "48bb3e53-bfca-4298-bab5-1627ca216739"

# Criar segunda persona
data = {
    "companyName": "Minha Segunda Empresa",
    "industry": "Marketing",
    "companySize": "1-10",
    "targetAudience": "Pequenas empresas",
    "primaryGoal": "Vendas",
    "mainChallenge": "Conversão",
    "channels": ["social"],
    "enrichmentLevel": "quick"
}

response = requests.post(
    f"http://localhost:3001/api/persona/create",  # Via Express (com auth)
    json=data
)

print(f"Status: {response.status_code}")
if response.status_code == 201:
    print("✅ Segunda persona criada!")
else:
    print(f"Resposta: {response.text[:200]}")
EOF
```

**OU deletar persona atual e refazer onboarding:**

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))

async def delete_current():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        await conn.execute("""
            DELETE FROM user_personas
            WHERE user_id = $1
        """, "48bb3e53-bfca-4298-bab5-1627ca216739")
        print("✅ Persona atual deletada")
        print("   Agora você pode fazer onboarding novamente!")
    finally:
        await conn.close()

asyncio.run(delete_current())
EOF
```

---

## 🎯 TESTE 3: VERIFICAR ENRICHMENT

### **Verificar Status:**

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))

async def check_status():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        p = await conn.fetchrow("""
            SELECT enrichment_status, research_completeness, last_enriched_at
            FROM user_personas
            WHERE user_id = $1
        """, "48bb3e53-bfca-4298-bab5-1627ca216739")
        
        print("📊 Status do Enrichment:")
        print(f"   Status: {p['enrichment_status']}")
        print(f"   Progresso: {p['research_completeness']}%")
        print(f"   Último: {p['last_enriched_at']}")
        print()
        
        if p['enrichment_status'] == 'pending':
            print("⏳ Enrichment ainda não iniciou")
        elif p['enrichment_status'] == 'processing':
            print("⚙️ Enrichment RODANDO!")
        elif p['enrichment_status'] == 'completed':
            print("✅ Enrichment COMPLETO!")
        elif p['enrichment_status'] == 'failed':
            print("❌ Enrichment FALHOU!")
    finally:
        await conn.close()

asyncio.run(check_status())
EOF
```

---

## 🎯 TESTE 4: INICIAR ENRICHMENT MANUALMENTE

Se enrichment não iniciou automaticamente:

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import requests

# Buscar sua persona atual
response = requests.get(
    "http://localhost:3001/api/persona/current"
)

if response.status_code == 200:
    persona = response.json()
    if persona:
        print(f"Sua persona ID: {persona['id']}")
        
        # Iniciar enrichment
        enrich = requests.post(
            "http://localhost:3001/api/persona/enrich/background",
            json={
                "personaId": persona['id'],
                "mode": "quick"
            }
        )
        
        print(f"Enrichment: {enrich.status_code}")
        if enrich.status_code == 202:
            print("✅ Enrichment iniciado!")
            print("   Aguarde ~40 segundos")
        else:
            print(f"Erro: {enrich.text}")
    else:
        print("Nenhuma persona encontrada")
else:
    print(f"Erro ao buscar persona: {response.status_code}")
    print("Você está logado? Tente fazer login primeiro")
EOF
```

---

## 🔍 TESTE 5: VERIFICAR MÓDULOS ENRICHED

Após enrichment completar, verificar se os dados foram salvos:

```bash
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))

async def check_modules():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        p = await conn.fetchrow("""
            SELECT 
                psychographic_core,
                buyer_journey,
                strategic_insights,
                enrichment_status
            FROM user_personas
            WHERE user_id = $1
        """, "48bb3e53-bfca-4298-bab5-1627ca216739")
        
        print("📊 Módulos Enriched:")
        print(f"   Status: {p['enrichment_status']}")
        print(f"   Psychographic Core: {'✅ SIM' if p['psychographic_core'] else '❌ NÃO'}")
        print(f"   Buyer Journey: {'✅ SIM' if p['buyer_journey'] else '❌ NÃO'}")
        print(f"   Strategic Insights: {'✅ SIM' if p['strategic_insights'] else '❌ NÃO'}")
        
    finally:
        await conn.close()

asyncio.run(check_modules())
EOF
```

---

## 📊 DIAGNÓSTICO ATUAL:

### **Sua Persona Atual:**
```
✅ Criada: SIM
✅ User ID: 48bb3e53-bfca-4298-bab5-1627ca216739 (correto!)
✅ Empresa: Cognita AI - Gabriel Lima
✅ Visível: SIM (você consegue ver no dashboard)
⏳ Enrichment: PENDING (não iniciou ainda)
```

### **Por que enrichment não rodou:**

O enrichment deveria ter sido chamado no **onboarding final**, mas pode não ter executado corretamente.

**Possíveis causas:**
1. Background task não executou
2. API keys faltando
3. Erro silencioso na execução

---

## 🛠️ SOLUÇÃO TEMPORÁRIA:

### **Opção 1: Iniciar Enrichment Manualmente**

Vou criar um botão no dashboard para você clicar e iniciar o enrichment.

### **Opção 2: Deletar e Refazer**

```bash
# Deletar persona atual
cd /Users/gabriellima/Downloads/Andromeda/advisory_replit
python3 << 'EOF'
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))

async def reset():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        await conn.execute("""
            DELETE FROM user_personas
            WHERE user_id = $1
        """, "48bb3e53-bfca-4298-bab5-1627ca216739")
        
        # Também resetar onboarding
        await conn.execute("""
            UPDATE onboarding_status
            SET is_completed = FALSE, completed_at = NULL
            WHERE user_id = $1
        """, "48bb3e53-bfca-4298-bab5-1627ca216739")
        
        print("✅ Persona deletada")
        print("✅ Onboarding resetado")
        print()
        print("Agora:")
        print("1. Faça logout")
        print("2. Faça login novamente")
        print("3. Complete onboarding")
        print("4. Persona será criada automaticamente")
    finally:
        await conn.close()

asyncio.run(reset())
EOF
```

Depois: http://localhost:3000/onboarding

---

## 🎯 PRÓXIMOS PASSOS (ANDROMEDA):

Vou agora:

1. **Investigar** por que background task não roda
2. **Corrigir** o enrichment background
3. **Adicionar botão** "Iniciar Enrichment" no dashboard
4. **Testar** end-to-end

---

## 🌐 ACESSE ENQUANTO ISSO:

Você JÁ pode:
- ✅ Ver sua persona: http://localhost:3000/persona-dashboard
- ✅ Usar o sistema (experts, chat, conselho)
- ✅ Criar conversas com experts

Apenas o **enrichment automático** que precisa de correção!

---

**Me diga:** Quer que eu corrija o enrichment agora ou você quer testar outras coisas primeiro? 😊

