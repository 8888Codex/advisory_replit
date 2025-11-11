#!/usr/bin/env python3
"""
Script para criar tabelas faltantes no banco Neon
"""
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def create_missing_tables():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # invite_codes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS invite_codes (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(16) NOT NULL UNIQUE,
                creator_id VARCHAR NOT NULL,
                used_by VARCHAR,
                used_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela invite_codes criada")
        
        # onboarding_status
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_status (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL UNIQUE,
                current_step INTEGER NOT NULL DEFAULT 0,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                business_info_completed BOOLEAN NOT NULL DEFAULT FALSE,
                persona_created BOOLEAN NOT NULL DEFAULT FALSE,
                first_chat_completed BOOLEAN NOT NULL DEFAULT FALSE,
                council_explored BOOLEAN NOT NULL DEFAULT FALSE,
                onboarding_data JSON,
                started_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """)
        print("✓ Tabela onboarding_status criada")
        
        # password_reset_tokens
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                token VARCHAR NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela password_reset_tokens criada")
        
        # login_audit
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS login_audit (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                success BOOLEAN NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                attempt_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela login_audit criada")
        
        # audit_logs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id VARCHAR,
                details JSON,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela audit_logs criada")
        
        # feature_flags
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                feature_name TEXT NOT NULL UNIQUE,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela feature_flags criada")
        
        # api_costs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS api_costs (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR,
                expert_id VARCHAR,
                conversation_id VARCHAR,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela api_costs criada")
        
        # content_flags
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS content_flags (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                message_id VARCHAR NOT NULL,
                flagged_by VARCHAR NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewed_by VARCHAR,
                reviewed_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela content_flags criada")
        
        # council_sessions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS council_sessions (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                topic TEXT NOT NULL,
                context JSON,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """)
        print("✓ Tabela council_sessions criada")
        
        # council_participants
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS council_participants (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR NOT NULL,
                expert_id VARCHAR NOT NULL,
                role TEXT,
                joined_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela council_participants criada")
        
        # council_insights
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS council_insights (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR NOT NULL,
                insight_type TEXT NOT NULL,
                content TEXT NOT NULL,
                expert_ids JSON,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela council_insights criada")
        
        # expert_collaboration_graph
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expert_collaboration_graph (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                expert_1_id VARCHAR NOT NULL,
                expert_2_id VARCHAR NOT NULL,
                collaboration_count INTEGER NOT NULL DEFAULT 1,
                synergy_score NUMERIC(3, 2),
                last_collaboration TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela expert_collaboration_graph criada")
        
        # user_profiles_extended
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles_extended (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL UNIQUE,
                company_name TEXT,
                company_size TEXT,
                industry TEXT,
                role TEXT,
                goals JSON,
                preferences JSON,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela user_profiles_extended criada")
        
        # user_personas (unificada com enrichment)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_personas (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                name TEXT NOT NULL,
                business_type TEXT,
                target_audience TEXT,
                main_challenges JSON,
                current_channels JSON,
                budget_range TEXT,
                experience_level TEXT,
                industry TEXT,
                enrichment_status TEXT DEFAULT 'pending',
                enrichment_level TEXT,
                enriched_at TIMESTAMP,
                youtube_research JSON,
                video_insights JSON,
                campaign_references JSON,
                inspiration_videos JSON,
                content_preferences JSON,
                research_completeness INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela user_personas criada")
        
        # user_activity
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data JSON,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("✓ Tabela user_activity criada")
        
        # user_favorites
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR NOT NULL,
                expert_id VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, expert_id)
            )
        """)
        print("✓ Tabela user_favorites criada")
        
        # Verificar tabelas criadas
        result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\n✅ Total de tabelas no banco: {len(result)}")
        for row in result:
            print(f"  - {row['table_name']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_missing_tables())

