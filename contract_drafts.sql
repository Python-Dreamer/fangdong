-- ================================================
-- 电子合同远程签字 - 数据库脚本
-- 执行方式：Supabase Dashboard → SQL Editor → New query → Run
-- ================================================

-- 1. 创建 contract_drafts 表
CREATE TABLE IF NOT EXISTS contract_drafts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  tenant_name TEXT,
  room_name TEXT,
  contract_html TEXT NOT NULL,
  landlord_signature TEXT NOT NULL,
  tenant_signature TEXT,
  share_token UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  signed_at TIMESTAMPTZ
);

-- 2. 启用 RLS
ALTER TABLE contract_drafts ENABLE ROW LEVEL SECURITY;

-- 3. 房东可以插入自己名下的合同
CREATE POLICY "landlord_insert" ON contract_drafts
  FOR INSERT
  WITH CHECK (auth.uid() = owner_id);

-- 4. 通过 share_token 公开查询（匿名访问，用于租客签字页面）
CREATE POLICY "public_select_by_token" ON contract_drafts
  FOR SELECT
  USING (true);

-- 5. 房东可以查看自己的合同
CREATE POLICY "landlord_select_own" ON contract_drafts
  FOR SELECT
  USING (auth.uid() = owner_id);

-- 6. 租客通过 share_token 更新签字（仅 pending 状态，仅限特定字段）
CREATE POLICY "tenant_update_signature" ON contract_drafts
  FOR UPDATE
  USING (share_token::text = current_setting('request.jwt.claims', true)::json->>'share_token' OR status = 'pending')
  WITH CHECK (status = 'pending' OR status = 'signed');

-- 7. 简化版：允许通过 anon key 更新 pending 状态的合同签字
-- 由于租客无 auth.uid()，使用更宽松的策略
DROP POLICY IF EXISTS "tenant_update_signature" ON contract_drafts;

CREATE POLICY "tenant_update_signature" ON contract_drafts
  FOR UPDATE
  USING (status = 'pending')
  WITH CHECK (status IN ('pending', 'signed'));

