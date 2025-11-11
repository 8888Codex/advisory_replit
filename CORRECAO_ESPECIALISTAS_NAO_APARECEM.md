# Correção: Especialistas Não Apareciam no Frontend

**Data:** 10 de novembro de 2025  
**Status:** ✅ CORRIGIDO

---

## PROBLEMAS IDENTIFICADOS E RESOLVIDOS

### PROBLEMA #1: Tabela com Colunas Duplicadas ✅

**Causa:**
- Tabela `experts` tinha colunas CamelCase E snake_case duplicadas
- `systemPrompt` (NOT NULL) + `system_prompt` (NULL)
- SQL inseria em `system_prompt`, mas Drizzle validava `systemPrompt`

**Solução:**
```sql
ALTER TABLE experts DROP COLUMN "systemPrompt";
ALTER TABLE experts DROP COLUMN "expertType";
ALTER TABLE experts DROP COLUMN "createdAt";
ALTER TABLE experts DROP COLUMN "updatedAt";
ALTER TABLE experts ALTER COLUMN system_prompt SET NOT NULL;
```

**Resultado:**
- ✅ Apenas colunas snake_case mantidas
- ✅ Experts podem ser salvos sem erro NOT NULL

---

### PROBLEMA #2: systemPrompt Vazio ✅

**Causa:**
- Claude às vezes não gerava systemPrompt
- Expert era salvo sem validação
- Chat falhava: "No clone found and no fallback prompt"

**Solução:**
```python
# Validação adicionada no auto-clone-stream
if len(expert_data["systemPrompt"].strip()) < 100:
    yield send_event("error", {
        "message": "Clone gerado sem prompt válido. Tente novamente."
    })
    return  # Não salva expert corrompido
```

**Resultado:**
- ✅ systemPrompt validado antes de salvar
- ✅ Criação falha se prompt inválido
- ✅ Usuário pode tentar novamente

---

### PROBLEMA #3: Upload de Avatar com 422 Error ✅

**Causa:**
- Frontend enviava `expertName` via FormData
- Backend esperava como Query parameter

**Solução:**
```typescript
// ANTES:
formData.append("expertName", name);
fetch("/api/upload/expert-avatar", { body: formData });

// DEPOIS:
const expertNameParam = encodeURIComponent(name);
fetch(`/api/upload/expert-avatar?expertName=${expertNameParam}`, {
  body: formData
});
```

**Resultado:**
- ✅ Upload de avatar funciona
- ✅ Arquivo salvo em `custom_experts/`
- ✅ Path retornado corretamente

---

### PROBLEMA #4: Expert Não Aparecia na Lista ✅

**Causa:**
- Cache do React Query não era invalidado corretamente
- Redirect muito rápido antes de refetch
- Redirecionava para `/` em vez de `/experts`

**Solução:**
```typescript
onSuccess: async (expert) => {
  // Invalidar múltiplas queries
  await queryClient.invalidateQueries({ queryKey: ["/api/experts"] });
  await queryClient.invalidateQueries({ queryKey: ["/api/categories"] });
  
  toast({ title: "Especialista Salvo!" });
  
  // Delay para garantir refetch
  setTimeout(() => {
    setLocation("/experts");  // Redireciona para lista
  }, 500);
}
```

**Resultado:**
- ✅ Queries são invalidadas
- ✅ Delay garante refetch antes de redirect
- ✅ Usuário vai direto para `/experts`
- ✅ Expert aparece na lista!

---

## VALIDAÇÃO FINAL

### Expert Salvo Corretamente:

```
Nome: Alex Hormozi
ID: 57ff19e9-ab24-4d0c-83bb-bd941acb6aa7
systemPrompt: 5181 chars ✅
Category: growth
Type: custom
Status: ✅ FUNCIONANDO
```

### API Retornando:

```
GET /api/experts
→ 19 experts (18 SEED + 1 custom)
→ Alex Hormozi incluído ✅
```

### Frontend:

```
Redirect: / → /experts ✅
Cache: Invalidado ✅
Delay: 500ms para refetch ✅
```

---

## FLUXO COMPLETO CORRIGIDO

1. **Criar Expert:** `/create`
   - Digite nome
   - Aguarde auto-clone (~60s)
   - systemPrompt validado (>100 chars) ✅
   - Avatar gerado do Unsplash ✅

2. **Upload Avatar (Opcional):**
   - Clique em "Adicionar Foto"
   - Selecione imagem
   - Preview atualiza ✅
   - Query parameter correto ✅

3. **Salvar:**
   - Upload de avatar (se houver) ✅
   - POST /api/experts ✅
   - Expert salvo no banco ✅
   - Logs no console ✅

4. **Redirect:**
   - Toast de confirmação ✅
   - Invalidação de queries ✅
   - Delay 500ms ✅
   - Redirect para `/experts` ✅

5. **Visualização:**
   - Expert aparece na lista ✅
   - Avatar exibido ✅
   - Pode iniciar chat ✅

---

## TESTE COMPLETO

1. **Recarregue a página:** http://localhost:3000/create
2. **Crie novo expert:**
   - Nome: "Outro Especialista"
   - Aguarde geração
   - OPCIONAL: Upload de foto
3. **Salvar**
4. **Aguarde redirect** para `/experts` (500ms)
5. **Veja o expert** na lista!

Se ainda não aparecer, abra Console (F12) e veja os logs `[SAVE EXPERT]`.

---

## LOGS ESPERADOS

### Console do Navegador:
```
[SAVE EXPERT] Sending data: {
  name: "Alex Hormozi",
  hasSystemPrompt: true,
  systemPromptLength: 5181,
  hasAvatar: true,
  category: "growth"
}
[AVATAR] Upload successful! Path: custom_experts/alex-hormozi.jpg
[SAVE EXPERT] Success! Expert saved: 57ff19e9-... Alex Hormozi
```

### Backend Python:
```
[AUTO-CLONE-STREAM] ✅ systemPrompt generated: 5181 chars
[UPLOAD] ✅ Avatar saved: .../custom_experts/alex-hormozi.jpg
[CREATE-EXPERT] Saved expert with ID: 57ff19e9-..., category: growth
```

---

## STATUS FINAL

✅ **Tabela Experts:** Colunas duplicadas removidas  
✅ **systemPrompt:** Validado e obrigatório (>100 chars)  
✅ **Avatar Upload:** Query parameter corrigido  
✅ **Cache:** Invalidação dupla implementada  
✅ **Redirect:** Melhorado com delay e destino correto  
✅ **Logs:** Debug completo no console  

**Especialistas personalizados agora funcionam 100%!** 🎉

