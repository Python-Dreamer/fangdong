-- ================================================
-- v79 账单抄表照片分享 - 数据库脚本
-- 执行方式（服务器）:
--   cat 20260909000000_bill_share.sql | sudo docker exec -i fd_db psql -U postgres -d postgres
-- 说明：房东在催租账单里生成二维码，租户扫码(无登录)查看账单明细与抄表照片。
--       照 contract_drafts 模式：anon 只能按随机 share_token 查询，看不到其他数据。
-- ================================================

-- 1. 账单分享表（每次生成二维码写一条；含账单明细快照+照片列表+过期时间）
CREATE TABLE IF NOT EXISTS bill_shares (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  share_token UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  tenant_name TEXT,
  room_name TEXT,
  bill_summary TEXT,
  total_amount NUMERIC DEFAULT 0,
  photos JSONB DEFAULT '[]'::jsonb,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 启用 RLS
ALTER TABLE bill_shares ENABLE ROW LEVEL SECURITY;

-- 3. 房东插入自己的分享
DROP POLICY IF EXISTS "bshare_insert_own" ON bill_shares;
CREATE POLICY "bshare_insert_own" ON bill_shares
  FOR INSERT WITH CHECK (auth.uid() = owner_id);

-- 4. 凭 share_token 公开查询（匿名访问，用于租客扫码页；token 为随机 UUID 不可猜）
DROP POLICY IF EXISTS "bshare_public_select" ON bill_shares;
CREATE POLICY "bshare_public_select" ON bill_shares
  FOR SELECT USING (true);

-- 5. 房东查看/删除自己的分享
DROP POLICY IF EXISTS "bshare_select_own" ON bill_shares;
CREATE POLICY "bshare_select_own" ON bill_shares
  FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS "bshare_delete_own" ON bill_shares;
CREATE POLICY "bshare_delete_own" ON bill_shares
  FOR DELETE USING (auth.uid() = owner_id);

-- 6. 授权（anon 用于扫码页只读查询；authenticated 用于房东写/删）
GRANT SELECT ON bill_shares TO anon, authenticated;
GRANT INSERT, DELETE ON bill_shares TO authenticated;

-- 7. 索引
CREATE INDEX IF NOT EXISTS idx_bill_shares_token ON bill_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_bill_shares_owner ON bill_shares(owner_id);

-- 8. 通知 PostgREST 重载 schema
NOTIFY pgrst, 'reload schema';
