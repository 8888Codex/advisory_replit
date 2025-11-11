-- ============================================
-- Script para Criar Usuário Inicial em Produção
-- ============================================
-- Execute este SQL no banco de dados do Dokploy

-- 1. Verificar se tabela users existe
SELECT COUNT(*) FROM users;

-- 2. Ver usuários existentes (se houver)
SELECT id, username, email, role FROM users LIMIT 5;

-- 3. Criar usuário SuperAdmin
-- Senha: admin123 (você pode trocar depois no sistema)
INSERT INTO users (username, email, password, role, created_at)
VALUES (
    'admin',
    'admin@oconselho.com',  -- TROQUE PELO SEU EMAIL
    '$2b$12$LQv3c1yqBWVHxkKGnMEqKueSXvAEqHcqhKUE.RLhQmW6hKGLLWqGe',  -- bcrypt hash de 'admin123'
    'superadmin',
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 4. Verificar se foi criado
SELECT id, username, email, role, created_at 
FROM users 
WHERE email = 'admin@oconselho.com';

-- ============================================
-- CREDENCIAIS PARA PRIMEIRO LOGIN:
-- ============================================
-- Email: admin@oconselho.com
-- Senha: admin123
--
-- ⚠️ IMPORTANTE: Mude a senha após o primeiro login!
-- ============================================

