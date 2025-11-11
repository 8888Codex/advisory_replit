#!/usr/bin/env python3
import asyncio
import asyncpg
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")

async def create_first_invite():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Gerar código único
        code = secrets.token_urlsafe(12)[:16].upper().replace("-", "").replace("_", "")
        
        # Criar código de convite com creator_id "system"
        result = await conn.fetchrow("""
            INSERT INTO invite_codes (id, code, creator_id, created_at)
            VALUES (gen_random_uuid(), $1, 'system', NOW())
            RETURNING id, code, creator_id, created_at
        """, code)
        
        print("=" * 50)
        print("🎉 CÓDIGO DE CONVITE CRIADO COM SUCESSO!")
        print("=" * 50)
        print()
        print(f"📋 Código de Convite: {result['code']}")
        print()
        print("✅ Use este código para criar sua conta!")
        print()
        print("Passos:")
        print("1. Acesse: http://localhost:3000")
        print("2. Clique em 'Criar Conta' ou 'Registrar'")
        print("3. Cole este código quando solicitado")
        print()
        print("=" * 50)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_first_invite())

