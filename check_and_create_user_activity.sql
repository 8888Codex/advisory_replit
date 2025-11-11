-- Check if user_activity table exists
SELECT EXISTS (
   SELECT FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name = 'user_activity'
);

-- If not exists, create it
CREATE TABLE IF NOT EXISTS user_activity (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    activity_type TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS user_activity_user_id_idx ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS user_activity_type_idx ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS user_activity_created_at_idx ON user_activity(created_at);

-- Verify table was created
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_activity'
ORDER BY ordinal_position;
