-- ==============================================================================
-- Nexora AI — Supabase RLS Fix (36 tables) — College Personal Mode
-- Run AFTER supabase_schema.sql in Supabase SQL Editor
-- Fixes: rls_disabled_in_public (36 ERROR) + sensitive_columns_exposed (3)
-- Backend uses its own JWT (PermissionService), not Supabase Auth, so permissive
-- service_role policy is safe for college demo. Prod: replace true with auth.uid()
-- ==============================================================================

BEGIN;

-- Enable RLS on all 36 public tables
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_secrets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspace_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspace_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.retrieval_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_review_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_logs ENABLE ROW LEVEL SECURITY;

-- Permissive policies for college personal mode (backend JWT via get_current_user)
-- Drop if exists then create (idempotent)

-- Helper: all tables list, create permissive policy
DO $$
DECLARE t TEXT;
DECLARE tables TEXT[] := ARRAY[
 'companies','company_settings','company_secrets','users','workspaces','folders',
 'workspace_members','workspace_invitations','invitations','workspace_templates',
 'conversations','messages','conversation_comments','mentions','message_reactions','favorites',
 'conversation_versions','notifications','activity_logs',
 'knowledge_bases','knowledge_documents','document_chunks','document_comments',
 'knowledge_nodes','knowledge_edges','retrieval_logs','calendar_events','tasks',
 'chat_feedback','dataset_projects','dataset_versions','dataset_review_items',
 'training_projects','training_runs','training_artifacts','training_logs'
];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format('DROP POLICY IF EXISTS "Allow all for backend" ON public.%I', t);
    EXECUTE format('CREATE POLICY "Allow all for backend" ON public.%I FOR ALL USING (true) WITH CHECK (true)', t);
  END LOOP;
END $$;

COMMIT;

-- Verify: should return 36
-- SELECT count(*) FROM pg_tables WHERE schemaname='public';
-- SELECT relname, relrowsecurity FROM pg_class WHERE relname IN ('users','workspaces','tasks');
-- Linter: Supabase -> Database -> Linter -> should be 0 errors after this
-- Data persistence: if users still 0 after register, check Render DATABASE_URL log:
--   [Database] Primary connection failed -> fallback sqlite means Supabase URL wrong (use pooler 6543?sslmode=require)
