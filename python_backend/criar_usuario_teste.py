"""
Script para criar usuário de teste e configurar tudo

USO: python criar_usuario_teste.py
"""

import asyncio
import asyncpg
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import bcrypt

load_dotenv(Path("../.env"))

async def criar_tudo():
    print("🔧 CRIANDO USUÁRIO E PERSONA DE TESTE")
    print("=" * 64)
    print()
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # 1. Verificar se já existe
        user = await conn.fetchrow("""
            SELECT id, email FROM users 
            WHERE email = 'teste@deploy.com.br'
        """)
        
        if user:
            print("✅ Usuário já existe!")
            user_id = user['id']
            print(f"   ID: {user_id}")
            print(f"   Email: {user['email']}")
        else:
            # 2. Criar usuário
            print("1️⃣ Criando usuário...")
            
            user_id = str(uuid.uuid4())
            email = "teste@deploy.com.br"
            password = "teste123"
            
            # Hash da senha
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            await conn.execute("""
                INSERT INTO users (id, username, email, password, role, available_invites, created_at)
                VALUES ($1, $2, $3, $4, 'user', 5, NOW())
            """, user_id, "teste_deploy", email, password_hash)
            
            print(f"   ✅ Criado!")
            print(f"   ID: {user_id}")
            print(f"   Email: {email}")
        
        print()
        
        # 3. Verificar se já tem persona
        persona = await conn.fetchrow("""
            SELECT id, company_name, enrichment_status 
            FROM user_personas 
            WHERE user_id = $1
        """, user_id)
        
        if persona:
            print("✅ Persona já existe!")
            print(f"   ID: {persona['id']}")
            print(f"   Empresa: {persona['company_name']}")
            print(f"   Status: {persona['enrichment_status']}")
            persona_id = persona['id']
        else:
            # 4. Criar persona
            print("2️⃣ Criando persona...")
            
            persona_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO user_personas (
                    id, user_id, company_name, industry, company_size,
                    target_audience, primary_goal, main_challenge,
                    channels, enrichment_level, enrichment_status,
                    research_mode, research_completeness, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW()
                )
            """,
                persona_id,
                user_id,
                "Empresa de Deploy",
                "Tecnologia",
                "11-50",
                "Empresas B2B",
                "Crescimento",
                "Leads qualificados",
                '["social", "email"]',  # JSON string
                "quick",
                "pending",
                "quick",
                0
            )
            
            print(f"   ✅ Criada!")
            print(f"   ID: {persona_id}")
        
        print()
        print("=" * 64)
        print()
        print("🎉 TUDO PRONTO!")
        print()
        print("📝 CREDENCIAIS PARA LOGIN:")
        print(f"   Email: teste@deploy.com.br")
        print(f"   Senha: teste123")
        print()
        print("🌐 ACESSE:")
        print(f"   http://localhost:3000/login")
        print()
        print("Depois de logar:")
        print(f"   1. Vá para: http://localhost:3000/persona-dashboard")
        print(f"   2. Clique em 'Enriquecer Persona' se ainda não enriched")
        print(f"   3. Aguarde ~45 segundos")
        print(f"   4. Veja os 9 módulos completos!")
        print()
        print("=" * 64)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(criar_tudo())

