-- Database Schema Modifications for Recallo Chat System
-- This script updates the database schema to properly support conversation management

-- 1. Remove the unnecessary message_id column from conversations table
-- (This column was confusing and not needed for conversation management)
ALTER TABLE public.conversations DROP COLUMN IF EXISTS message_id;

-- 2. Add foreign key constraint from chat_logs to conversations
-- This ensures data integrity between conversations and their messages
ALTER TABLE public.chat_logs 
ADD CONSTRAINT fk_conversation 
FOREIGN KEY (conversation_id) REFERENCES public.conversations(conversation_id) ON DELETE CASCADE;

-- 3. Add index on conversation_id in chat_logs for better performance
-- This will speed up queries when fetching messages for a specific conversation
CREATE INDEX IF NOT EXISTS idx_chat_logs_conversation_id 
ON public.chat_logs USING btree (conversation_id);

-- 4. Verify the final schema structure
-- Conversations table should now have:
-- - conversation_id (uuid, primary key)
-- - user_id (uuid, foreign key to users)
-- - title (text, default 'New Chat')
-- - created_at (timestamp)
-- - updated_at (timestamp)

-- Chat logs table should have:
-- - id (serial, primary key)
-- - user_message (text)
-- - response_message (text)
-- - created_at (timestamp)
-- - user_id (uuid, foreign key to users)
-- - conversation_id (uuid, foreign key to conversations)
-- - message_id (uuid, for individual message tracking)

-- 5. Optional: Clean up any orphaned chat_logs that don't have valid conversation_ids
-- Uncomment the following lines if you want to clean up existing data:
-- DELETE FROM public.chat_logs 
-- WHERE conversation_id IS NOT NULL 
-- AND conversation_id NOT IN (SELECT conversation_id FROM public.conversations);

COMMIT;
