# 🎯 Sistema de Conselho e Recomendações

**Status:** ✅ Funcionando  
**Data:** 10 de novembro de 2025  

---

## 🌟 O QUE É O SISTEMA DE CONSELHO?

O sistema possui **3 níveis** de recomendação de experts:

### 1. **Recomendações por Perfil** (Simples)
- **Endpoint:** `GET /api/experts/recommendations`
- **Como funciona:** Baseado no seu perfil de negócio (indústria, objetivos, desafios)
- **Retorna:** Todos os 40 experts ranqueados por relevância (1-5 estrelas)
- **Velocidade:** Instantâneo

### 2. **Análise Inteligente** (Avançado)  
- **Endpoint:** `POST /api/recommend-experts`
- **Como funciona:** IA analisa seu problema específico e recomenda os melhores experts
- **Retorna:** Top 3-5 experts com justificativas detalhadas
- **Velocidade:** 3-5 segundos

### 3. **Conselho Colaborativo** (Premium)
- **Endpoint:** `POST /api/council/analyze`
- **Como funciona:** 8 experts analisam juntos e geram consenso
- **Retorna:** Análises individuais + síntese final
- **Velocidade:** 30-60 segundos
- **Versão Streaming:** `/api/council/analyze-stream` (tempo real)

---

## 📡 APIs Disponíveis:

### 1. GET /api/experts/recommendations

**Descrição:** Recomendações baseadas em perfil de negócio

**Resposta:**
```json
{
  "hasProfile": false,
  "recommendations": [
    {
      "expertId": "uuid",
      "expertName": "Dan Kennedy",
      "score": 85,
      "stars": 5,
      "justification": "Especialista em marketing de resposta...",
      "breakdown": {
        "goal_alignment": 30,
        "industry_match": 25,
        "challenge_alignment": 20,
        "keyword_match": 10
      }
    }
  ]
}
```

### 2. POST /api/recommend-experts ⭐ Inteligente

**Body:**
```json
{
  "problem": "Preciso aumentar vendas online de produtos artesanais"
}
```

**Resposta:**
```json
{
  "recommendations": [
    {
      "expertId": "uuid",
      "expertName": "Dan Kennedy",
      "avatar": "url",
      "relevanceScore": 5,
      "stars": 5,
      "justification": "Especialista em marketing de resposta direta..."
    }
  ]
}
```

### 3. POST /api/council/analyze 🏆 Premium

**Body:**
```json
{
  "problem": "Como posso triplicar vendas nos próximos 6 meses?",
  "expertIds": ["seed-philip-kotler", "seed-seth-godin", "seed-dan-kennedy"]
}
```

**Resposta:**
```json
{
  "id": "analysis-uuid",
  "userId": "user-id",
  "problem": "Como posso triplicar...",
  "marketResearch": "Dados de pesquisa Perplexity...",
  "contributions": [
    {
      "expertId": "seed-philip-kotler",
      "expertName": "Philip Kotler",
      "analysis": "Análise completa...",
      "keyInsights": ["insight 1", "insight 2"],
      "recommendations": ["ação 1", "ação 2"]
    }
  ],
  "consensus": "Síntese final do conselho..."
}
```

### 4. POST /api/council/analyze-stream (SSE) 🚀

**Igual ao anterior, mas com streaming em tempo real!**

**Eventos emitidos:**
- `analysis_started` - Início
- `research_started` - Pesquisa Perplexity
- `research_completed` - Pesquisa finalizada
- `expert_started` - Expert começou análise
- `expert_completed` - Expert terminou
- `consensus_started` - Síntese iniciada
- `analysis_complete` - Análise final completa

---

## 💻 Como Usar no Frontend:

### Exemplo 1: Pedir Recomendações Simples

```typescript
// client/src/components/ExpertRecommendations.tsx

const { data } = useQuery({
  queryKey: ['/api/experts/recommendations'],
});

return (
  <div>
    {data?.recommendations
      .filter(rec => rec.stars >= 4)  // Apenas 4-5 estrelas
      .map(rec => (
        <ExpertCard
          key={rec.expertId}
          name={rec.expertName}
          stars={rec.stars}
          reason={rec.justification}
        />
      ))
    }
  </div>
);
```

### Exemplo 2: Análise Inteligente de Problema

```typescript
// client/src/components/SmartRecommendation.tsx

const { mutate: getRecommendations } = useMutation({
  mutationFn: async (problem: string) => {
    const res = await fetch('/api/recommend-experts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problem })
    });
    return res.json();
  },
  onSuccess: (data) => {
    // Mostra top 3-5 experts recomendados
    console.log('Recomendações:', data.recommendations);
  }
});

// Usar:
getRecommendations("Como aumentar conversão de vendas?");
```

### Exemplo 3: Conselho Colaborativo com Streaming

```typescript
// client/src/components/CouncilAnalysis.tsx

function startCouncilAnalysis(problem: string) {
  const eventSource = new EventSource(
    `/api/council/analyze-stream?problem=${encodeURIComponent(problem)}`
  );

  eventSource.addEventListener('expert_started', (e) => {
    const data = JSON.parse(e.data);
    console.log(`${data.expertName} está analisando...`);
  });

  eventSource.addEventListener('expert_completed', (e) => {
    const data = JSON.parse(e.data);
    console.log(`${data.expertName} terminou!`);
  });

  eventSource.addEventListener('analysis_complete', (e) => {
    const analysis = JSON.parse(e.data);
    console.log('Análise completa:', analysis);
    eventSource.close();
  });
}
```

---

## 🎨 Sugestão de UI:

### Tela de "Conselho Inteligente":

```
┌──────────────────────────────────────────────┐
│  🎯 Conselho Inteligente                     │
├──────────────────────────────────────────────┤
│                                              │
│  Descreva seu desafio de marketing:          │
│  ┌────────────────────────────────────────┐  │
│  │ Preciso aumentar vendas online...      │  │
│  │                                        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  [🧠 Analisar com IA]  [👥 Conselho Completo]│
│                                              │
│  ─────────────────────────────────────────   │
│                                              │
│  📊 Experts Recomendados:                    │
│                                              │
│  ⭐⭐⭐⭐⭐ Dan Kennedy                         │
│  Especialista em marketing de resposta       │
│  direta e copywriting de conversão...        │
│  [Conversar Agora]                           │
│                                              │
│  ⭐⭐⭐⭐⭐ Seth Godin                           │
│  Especialista em marketing de nicho...       │
│  [Conversar Agora]                           │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🔧 Testes:

### Teste 1: Recomendações Simples
```bash
curl "http://localhost:3000/api/experts/recommendations"
```

### Teste 2: Análise Inteligente
```bash
curl -X POST "http://localhost:3000/api/recommend-experts" \
  -H "Content-Type: application/json" \
  -d '{"problem": "Como melhorar meu SEO?"}'
```

### Teste 3: Conselho Completo  
```bash
curl -X POST "http://localhost:3000/api/council/analyze" \
  -H "Content-Type: application/json" \
  -d '{"problem": "Preciso de uma estratégia completa de marketing digital"}'
```

**NOTA:** O conselho completo pode levar 30-60 segundos!

---

## ✅ O QUE FOI CORRIGIDO:

1. ✅ Ordem das rotas FastAPI (específicas ANTES de parametrizadas)
2. ✅ Imports do `recommendation.py`
3. ✅ Teste de integração com IA
4. ✅ Sistema respondendo corretamente

---

## 🚀 PRÓXIMO PASSO:

**Acesse o sistema no navegador:**

```
http://localhost:3000
```

E teste a funcionalidade de **sugestão de conselho**!

- Se estiver visível → ✅ Perfeito!
- Se não estiver → Me avise e crio a interface!

---

**Criado por:** IA Assistant  
**Feature:** Sistema de Conselho Inteligente  
**Status:** Funcionando ✅

🎯 **TESTE AGORA NO NAVEGADOR!**

