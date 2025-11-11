# 🔍 PERPLEXITY INTEGRATION - Reddit Research

**Data:** 10 de novembro de 2025  
**Status:** ✅ IMPLEMENTADO E ATIVO

---

## 🎯 OBJETIVO

Integrar **pesquisa real do Reddit via Perplexity AI** no sistema de enriquecimento de personas para obter:

- 🗣️ **Linguagem autêntica** do público-alvo
- 💬 **Pain points reais** (não teóricos)
- 🎯 **Goals e valores** baseados em discussões reais
- 🌐 **Comunidades ativas** onde o público se reúne

---

## 🏗️ ARQUITETURA DA INTEGRAÇÃO

### **PHASE 0: Reddit Research (NOVO)**

```
Perplexity AI Sonar Model
  ↓
Analisa discussões reais do Reddit
  ↓
Extrai insights estruturados:
  - communities (subreddits relevantes)
  - painPoints (frustrações mencionadas)
  - goals (objetivos buscados)
  - values (valores que guiam decisões)
  - language (como se expressam)
  ↓
Passa como contexto para os módulos de IA
```

---

## 📊 FLUXO DE ENRIQUECIMENTO ATUALIZADO

### **1. PHASE 0: Reddit Research** (NOVO)
- ⏱️ ~10-15s
- 🔍 1 chamada à Perplexity API
- 📦 Retorna 5 comunidades + 8 pain points + 8 goals + 8 values

### **2. PHASE 1: YouTube Research** (Existente)
- ⏱️ ~15-20s
- 🎥 2-10 queries no YouTube API
- 📊 Insights gerados com Claude

### **3. PHASE 2: Deep Modules** (Melhorado)
- ⏱️ ~20-40s (quick) / ~2-3min (strategic)
- 🧠 Usa dados do Reddit + YouTube
- 🎨 3, 6 ou 8 módulos dependendo do nível

### **4. PHASE 3: Base Fields** (Otimizado)
- ⏱️ ~5-10s ou 0s se Reddit completo
- 📝 Usa dados do Reddit diretamente
- ✨ Claude só complementa se faltar itens

---

## ⚡ OTIMIZAÇÕES IMPLEMENTADAS

### **1. Reddit como Base** ✅
Se Perplexity retornar dados completos:
- Pain points do Reddit são usados diretamente
- Goals do Reddit são usados diretamente
- Values do Reddit são usados diretamente
- **Claude não é chamado** (economia!)

### **2. Hybrid Approach** ✅
Se Reddit retornar dados parciais:
- Usa o que o Reddit trouxe como base
- Claude completa apenas o que falta
- Melhor qualidade + menor custo

### **3. Contexto Rico** ✅
Todos os módulos recebem:
- Comunidades do Reddit (onde o público está)
- Pain points reais (do que reclamam)
- Linguagem autêntica (como falam)

---

## 🎨 EXEMPLO DE DADOS COLETADOS

```json
{
  "communities": [
    "r/marketing",
    "r/entrepreneur",
    "r/startups",
    "r/smallbusiness",
    "r/digital_marketing"
  ],
  "painPoints": [
    "Alto custo de aquisição de clientes",
    "Dificuldade em medir ROI de marketing",
    "Baixa taxa de conversão no funil",
    "Concorrência acirrada em leilões de ads",
    "Falta de diferenciação da marca",
    "Dificuldade em criar conteúdo relevante",
    "Equipe pequena e sobrecarregada",
    "Budget limitado para testes"
  ],
  "goals": [
    "Reduzir CAC em 30%",
    "Aumentar taxa de conversão",
    "Construir marca forte",
    "Gerar leads qualificados",
    "Automatizar processos",
    "Escalar operação",
    "Melhorar retenção de clientes",
    "Dominar SEO orgânico"
  ],
  "values": [
    "Eficiência e produtividade",
    "Data-driven decision making",
    "Autenticidade na comunicação",
    "ROI mensurável",
    "Crescimento sustentável",
    "Inovação e experimentação",
    "Transparência com clientes",
    "Foco no cliente"
  ],
  "language": "Tom direto e objetivo, uso de métricas e números, termos técnicos de marketing digital (CAC, LTV, funil, conversão), linguagem informal mas profissional"
}
```

---

## 🔑 VARIÁVEL DE AMBIENTE

```bash
# .env
PERPLEXITY_API_KEY=pplx-seu-token-aqui
```

✅ **Já configurada!**

---

## 🧪 COMO TESTAR

### **Teste 1: Criar Nova Persona**
```bash
1. Acesse /onboarding
2. Preencha com dados reais
3. Escolha nível Quick ou Strategic
4. Clique em Finalizar
5. Aguarde ~45s-2min
6. Veja nos logs do backend:
   [REDDIT] ✅ Coletou 5 comunidades
   [REDDIT] ✅ Coletou 8 pain points
```

### **Teste 2: Verificar Dados no Banco**
```sql
SELECT 
  company_name,
  pain_points,
  goals,
  values,
  communities
FROM user_personas
WHERE enrichment_status = 'completed'
ORDER BY created_at DESC
LIMIT 1;
```

### **Teste 3: Ver na Interface**
```
1. Vá para /personas
2. Clique em "Ver Detalhes" na persona enriquecida
3. Verifique se pain points são específicos e reais
4. Valores devem refletir linguagem do público
```

---

## 📈 COMPARAÇÃO: Antes vs Depois

### **ANTES (Só Claude)**
- Pain points genéricos baseados em indústria
- Goals teóricos
- Values assumidos
- Linguagem formal e genérica

### **DEPOIS (Reddit via Perplexity + Claude)**
- Pain points específicos mencionados nas comunidades
- Goals baseados em aspirações reais
- Values extraídos de discussões
- Linguagem autêntica do público
- Comunidades identificadas para marketing

---

## 💰 CUSTO ESTIMADO

**Perplexity API:**
- Modelo: `sonar` (lightweight)
- ~1 chamada por persona
- Custo: ~$0.001-0.002 por enriquecimento

**Economia no Claude:**
- Se Reddit fornecer 8/8 itens: **100% economia** no Phase 3
- Se Reddit fornecer 5/8 itens: **~60% economia** no Phase 3

**ROI:** Mais qualidade + menor custo! 📊

---

## ✅ STATUS DA IMPLEMENTAÇÃO

- ✅ Perplexity API configurada
- ✅ Reddit research integrado no Phase 0
- ✅ Contexto passado para todos os módulos
- ✅ Base fields otimizados (usa Reddit primeiro)
- ✅ Error handling robusto
- ✅ Logs detalhados
- ✅ Backend reiniciado e funcionando

---

## 🚀 PRÓXIMO PASSO

**TESTE AGORA!**

Crie uma nova persona para ver a integração Perplexity em ação:

1. Delete a persona antiga (se quiser)
2. Vá para /onboarding
3. Crie nova persona
4. Acompanhe os logs:
   ```bash
   tail -f /Users/gabriellima/Downloads/Andromeda/advisory_replit/backend_perplexity.log
   ```

**Você deve ver:**
```
[REDDIT] Chamando Perplexity API...
[REDDIT] ✅ Coletou 5 comunidades
[REDDIT] ✅ Coletou 8 pain points
```

**Integração Perplexity está ATIVA e funcionando!** 🎉

