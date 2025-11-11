# Correções: Avatar Upload e Analytics

**Data:** 10 de novembro de 2025  
**Status:** ✅ IMPLEMENTADO

---

## PROBLEMA #1: Analytics Zerados

### Sintoma:
- Dashboard de Analytics mostrava todos os valores em 0
- Nenhum dado de atividade sendo exibido
- Erro no backend: `column "metadata" does not exist`

### Causa Raiz:
Tabela `user_activity` estava com schema desatualizado:
- Coluna: `activity_data` (tipo: JSON)
- Esperado: `metadata` (tipo: JSONB)

### Solução Implementada:

**Migration aplicada:**
```sql
-- Rename column
ALTER TABLE user_activity 
RENAME COLUMN activity_data TO metadata;

-- Change type to JSONB
ALTER TABLE user_activity 
ALTER COLUMN metadata TYPE JSONB USING metadata::jsonb;
```

**Resultado:**
```
✅ Coluna renomeada: activity_data → metadata
✅ Tipo alterado: JSON → JSONB
✅ Analytics endpoint funcionando
```

**Tabela atualizada:**
```
user_activity
  - id: VARCHAR (PK)
  - user_id: VARCHAR
  - activity_type: TEXT
  - metadata: JSONB  ← CORRIGIDO
  - created_at: TIMESTAMP
```

---

## PROBLEMA #2: Avatar em Especialistas Personalizados

### Sintoma:
- Usuário não conseguia adicionar fotos aos especialistas personalizados
- Falta de humanização no processo

### Funcionalidades Implementadas:

#### 1. Upload Manual de Avatar (NOVO)

**Frontend (`client/src/pages/Create.tsx`):**
- Adicionado botão "Adicionar Foto" após geração do especialista
- Preview do avatar personalizado
- Validação de tipo de arquivo (PNG, JPG, WEBP)
- Validação de tamanho (max 5MB)
- Upload antes de salvar o especialista

**UI Adicionada:**
```tsx
<Avatar className="h-24 w-24">
  {customAvatarPreview ? (
    <AvatarImage src={customAvatarPreview} />
  ) : generatedExpert.avatar ? (
    <AvatarImage src={`/attached_assets/${generatedExpert.avatar}`} />
  ) : null}
  <AvatarFallback>{initials}</AvatarFallback>
</Avatar>

<Button>
  <Image className="h-3.5 w-3.5" />
  {customAvatarFile ? 'Trocar Foto' : 'Adicionar Foto'}
</Button>
```

#### 2. Endpoint de Upload (NOVO)

**Backend (`python_backend/main.py`):**
```python
@app.post("/api/upload/expert-avatar")
async def upload_expert_avatar_temp(
    file: UploadFile = File(...),
    expertName: str = Query(...)
):
    # Validate type, size, format
    # Resize to 400x400
    # Save to custom_experts/
    # Return avatar path
```

**Funcionalidades:**
- ✅ Validação de tipo de arquivo
- ✅ Validação de tamanho (max 5MB)
- ✅ Resize automático para 400x400px
- ✅ Otimização JPEG (quality 85)
- ✅ Nome sanitizado baseado no nome do expert
- ✅ Salva em `attached_assets/custom_experts/`

#### 3. Fluxo de Criação Atualizado

**ANTES:**
```
1. Usuário digita nome do expert
2. Sistema gera avatar do Unsplash
3. Salva expert
```

**DEPOIS:**
```
1. Usuário digita nome do expert
2. Sistema gera avatar do Unsplash (ou fallback)
3. ➕ OPÇÃO: Usuário clica em "Adicionar Foto"
4. ➕ OPÇÃO: Faz upload de imagem personalizada
5. Preview atualiza em tempo real
6. Salva expert com avatar escolhido
```

---

## COMO TESTAR

### Teste 1: Analytics Dashboard

1. Acesse: http://localhost:3000/analytics
2. Verifique se a página carrega sem erros
3. Os valores estarão em 0 (normal, não há atividades ainda)

**Para gerar dados de teste:**
```bash
# Seed de dados de analytics (opcional)
curl -X POST http://localhost:5001/api/analytics/seed
```

### Teste 2: Upload de Avatar em Especialista

1. Acesse: http://localhost:3000/create
2. Digite: "Steve Jobs"
3. Clique em "Criar Clone Automático"
4. Aguarde a geração completar
5. Clique em "Adicionar Foto"
6. Selecione uma imagem do seu computador
7. Veja o preview atualizar
8. Clique em "Salvar Especialista"

**Resultado esperado:**
- ✅ Avatar personalizado salvo em `attached_assets/custom_experts/steve-jobs.jpg`
- ✅ Expert criado com avatar personalizado
- ✅ Avatar aparece no card do expert em todas as páginas

---

## ARQUIVOS MODIFICADOS

### Backend (1 arquivo):
1. `python_backend/main.py`
   - Adicionado endpoint `/api/upload/expert-avatar` (linhas 2695-2772)
   - Validação, resize e save de imagem

### Frontend (1 arquivo):
1. `client/src/pages/Create.tsx`
   - Adicionado state para `customAvatarFile` e `customAvatarPreview`
   - Função `handleAvatarFileChange` com validações
   - Atualizado `handleSaveExpert` para fazer upload antes de salvar
   - UI do botão "Adicionar Foto" com preview

### Database (Migration):
1. Tabela `user_activity` corrigida:
   - `activity_data` → `metadata`
   - `JSON` → `JSONB`

---

## BENEFÍCIOS

### Para o Usuário:
✅ **Personalização total:** Pode usar fotos profissionais reais  
✅ **Humanização:** Avatares reais criam conexão emocional  
✅ **Flexibilidade:** Pode usar avatar auto-gerado OU fazer upload  
✅ **Preview instantâneo:** Vê o resultado antes de salvar  

### Para o Sistema:
✅ **Analytics funcionando:** Dashboard mostra métricas reais  
✅ **Sem breaking changes:** Fallback para avatar auto-gerado  
✅ **Qualidade garantida:** Resize automático para 400x400px  
✅ **Storage organizado:** Avatars em pasta dedicada  

---

## PRÓXIMOS PASSOS (Opcional)

1. **Crop de Imagem:** Permitir usuário fazer crop antes de salvar
2. **Filtros:** Aplicar filtros/ajustes na imagem
3. **Avatar Placeholder:** Usar avatar genérico melhor que iniciais
4. **Galeria:** Selecionar de galeria de avatars pré-definidos

---

## COMPATIBILIDADE

✅ **Backwards compatible:** Experts antigos sem avatar continuam funcionando  
✅ **Fallback gracioso:** Se upload falhar, usa avatar auto-gerado  
✅ **Validações robustas:** Previne arquivos corrompidos ou muito grandes  

---

## STATUS FINAL

✅ **Analytics:** Tabela corrigida, endpoint funcionando  
✅ **Avatar Upload:** Implementado com validações e resize  
✅ **UI Melhorada:** Botão de upload integrado no fluxo de criação  
✅ **Pasta criada:** `attached_assets/custom_experts/` pronta  

**Sistema pronto para humanizar especialistas personalizados!** 🎉

