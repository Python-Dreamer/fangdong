-- v86 需求5：房东自有租约模板库（纯增量：1张新表 contract_templates + 房东CRUD的RLS）
-- 执行方式：在服务器 sudo docker exec -i fd_db psql -U postgres -d postgres < 本文件
-- 幂等：可重复执行（IF NOT EXISTS / DROP POLICY IF EXISTS）
-- 说明：模板存 mammoth 把 docx 转成的 HTML（与现有电子合同流程一致）；
--   仅房东本人可读写自己的模板，不向员工/匿名开放。

CREATE TABLE IF NOT EXISTS contract_templates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  name TEXT NOT NULL,
  template_html TEXT NOT NULL,
  docx_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE contract_templates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ct_select_own ON contract_templates;
CREATE POLICY ct_select_own ON contract_templates FOR SELECT
  USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS ct_insert_own ON contract_templates;
CREATE POLICY ct_insert_own ON contract_templates FOR INSERT
  WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS ct_update_own ON contract_templates;
CREATE POLICY ct_update_own ON contract_templates FOR UPDATE
  USING (auth.uid() = owner_id) WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS ct_delete_own ON contract_templates;
CREATE POLICY ct_delete_own ON contract_templates FOR DELETE
  USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON contract_templates TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_ct_owner ON contract_templates(owner_id, created_at);

DROP TRIGGER IF EXISTS trg_ct_updated ON contract_templates;
CREATE TRIGGER trg_ct_updated BEFORE UPDATE ON contract_templates
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

NOTIFY pgrst, 'reload schema';
