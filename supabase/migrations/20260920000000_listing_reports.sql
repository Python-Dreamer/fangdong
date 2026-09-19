-- v95 租房页留言举报（纯增量：1张新表）
-- 执行方式：在服务器 docker exec fd_db psql -U postgres -d postgres
-- 幂等：可重复执行（IF NOT EXISTS / DROP POLICY IF EXISTS）
-- 安全：公开页举报人为匿名，禁止前端直写数据库；
--      仅 file_server.py 持 service_role 写入/查询，service_role 绕过 RLS。
--      因此 anon/authenticated 不授予该表任何权限。

CREATE TABLE IF NOT EXISTS listing_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id UUID NOT NULL,                 -- 被举报房源
  owner_id UUID,                          -- 被举报房东（后端回填，用于定位处罚）
  room_name TEXT DEFAULT '',              -- 举报时房源名快照
  reason VARCHAR(20) NOT NULL DEFAULT 'other',
        -- fake=虚假房源 scam=诈骗/收钱拉黑 rented=已出租/信息过期 wrong=图片价格不符 other=其他
  detail TEXT DEFAULT '',                 -- 举报人补充说明（<=500字）
  contact TEXT DEFAULT '',                -- 举报人选填联系方式（<=100字）
  reporter_ip TEXT DEFAULT '',            -- 后端记录，防刷溯源
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- pending=待处理 resolved=已处理(已下架/处罚) dismissed=已驳回
  handle_note TEXT DEFAULT '',
  handled_by UUID,
  handled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE listing_reports ENABLE ROW LEVEL SECURITY;

-- 显式不给 anon/authenticated 任何策略：默认全部拒绝。
-- （service_role 为表 owner 级超级角色，绕过 RLS，由 file_server.py 专用。）
DROP POLICY IF EXISTS listing_reports_deny_all ON listing_reports;

-- 撤销可能继承的默认权限，确保匿名用户无法直连读写
REVOKE ALL ON listing_reports FROM anon;
REVOKE ALL ON listing_reports FROM authenticated;

CREATE INDEX IF NOT EXISTS idx_listing_reports_status ON listing_reports(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_listing_reports_owner ON listing_reports(owner_id);
CREATE INDEX IF NOT EXISTS idx_listing_reports_room ON listing_reports(room_id);

-- 仅授予 service_role（file_server.py 专用）；角色不存在时静默跳过
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON listing_reports TO service_role';
  END IF;
END $$;
-- 自建库兜底：覆盖 file_server 可能使用的连库角色（角色不存在则跳过）
DO $$
DECLARE r TEXT;
BEGIN
  GRANT ALL ON listing_reports TO postgres;
  FOREACH r IN ARRAY ARRAY['service_role','authenticator','supabase_admin'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE 'GRANT SELECT, INSERT, UPDATE ON listing_reports TO ' || quote_ident(r);
    END IF;
  END LOOP;
END $$;
