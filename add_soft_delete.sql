-- Add soft delete support to critical tables
-- Run this migration to add deleted_at column for soft delete functionality

-- Conversations table
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at 
ON conversations(deleted_at);

-- User personas table  
ALTER TABLE user_personas
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_user_personas_deleted_at 
ON user_personas(deleted_at);

-- Experts table (custom experts only)
ALTER TABLE experts
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_experts_deleted_at 
ON experts(deleted_at);

-- Messages table
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_deleted_at 
ON messages(deleted_at);

-- Comments for documentation
COMMENT ON COLUMN conversations.deleted_at IS 'Soft delete timestamp. NULL = active, NOT NULL = deleted';
COMMENT ON COLUMN user_personas.deleted_at IS 'Soft delete timestamp. NULL = active, NOT NULL = deleted';
COMMENT ON COLUMN experts.deleted_at IS 'Soft delete timestamp. NULL = active, NOT NULL = deleted';
COMMENT ON COLUMN messages.deleted_at IS 'Soft delete timestamp. NULL = active, NOT NULL = deleted';

-- Success message
SELECT 'Soft delete columns added successfully!' AS status;

