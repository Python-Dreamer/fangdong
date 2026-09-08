-- ================================================
-- v76 中介员工提成模块
-- 3 张新表 + workspace_settings 开关字段
-- 纯增量，不改动任何现有表结构与逻辑（仅给设置表加一个默认关闭的开关列）
-- 执行方式：见部署脚本（自动探测 postgres 容器执行）
-- ================================================

-- 0. 开关字段：中介老板开启后才显示提成模块（普通房东默认关闭，无感知）
ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS commission_enabled BOOLEAN DEFAULT false;

-- 1. 员工表（中介业务员）
CREATE TABLE IF NOT EXISTS staff (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE staff ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS staff_select_own ON staff;
CREATE POLICY staff_select_own ON staff FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS staff_insert_own ON staff;
CREATE POLICY staff_insert_own ON staff FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS staff_update_own ON staff;
CREATE POLICY staff_update_own ON staff FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS staff_delete_own ON staff;
CREATE POLICY staff_delete_own ON staff FOR DELETE USING (auth.uid() = owner_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON staff TO anon, authenticated;
CREATE INDEX IF NOT EXISTS idx_staff_owner ON staff(owner_id, active);

-- 2. 租约提成配置（一个租约一条配置；租客不设提成则无记录）
CREATE TABLE IF NOT EXISTS tenant_commission (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
  mode VARCHAR(10) NOT NULL DEFAULT 'monthly',      -- monthly=按月计提 / onetime=一次性提成
  basis VARCHAR(10) NOT NULL DEFAULT 'effective',  -- effective=按租约生效 / received=按实收租金
  rate_type VARCHAR(10) NOT NULL DEFAULT 'percent',-- percent=按比例 / fixed=固定金额
  rate NUMERIC NOT NULL DEFAULT 0,                 -- 百分比(%) 或 固定金额(元)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id)
);
ALTER TABLE tenant_commission ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tcomm_select_own ON tenant_commission;
CREATE POLICY tcomm_select_own ON tenant_commission FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS tcomm_insert_own ON tenant_commission;
CREATE POLICY tcomm_insert_own ON tenant_commission FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS tcomm_update_own ON tenant_commission;
CREATE POLICY tcomm_update_own ON tenant_commission FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS tcomm_delete_own ON tenant_commission;
CREATE POLICY tcomm_delete_own ON tenant_commission FOR DELETE USING (auth.uid() = owner_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_commission TO anon, authenticated;
CREATE INDEX IF NOT EXISTS idx_tcomm_owner ON tenant_commission(owner_id);
CREATE INDEX IF NOT EXISTS idx_tcomm_staff ON tenant_commission(staff_id);

-- 3. 提成流水（系统自动生成，可标记已结算）
CREATE TABLE IF NOT EXISTS commission_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
  tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
  month VARCHAR(7),                    -- 提成月份 YYYY-MM（一次性提成为成交月）
  amount NUMERIC NOT NULL DEFAULT 0,   -- 提成金额
  base_amount NUMERIC NOT NULL DEFAULT 0,  -- 计提基数（月租金/实收金额）
  mode VARCHAR(10) NOT NULL DEFAULT 'monthly',
  basis VARCHAR(10) NOT NULL DEFAULT 'effective',
  settled BOOLEAN NOT NULL DEFAULT false,
  settled_at TIMESTAMPTZ,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE commission_records ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS crec_select_own ON commission_records;
CREATE POLICY crec_select_own ON commission_records FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS crec_insert_own ON commission_records;
CREATE POLICY crec_insert_own ON commission_records FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS crec_update_own ON commission_records;
CREATE POLICY crec_update_own ON commission_records FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS crec_delete_own ON commission_records;
CREATE POLICY crec_delete_own ON commission_records FOR DELETE USING (auth.uid() = owner_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON commission_records TO anon, authenticated;
CREATE INDEX IF NOT EXISTS idx_crec_owner_month ON commission_records(owner_id, month);
CREATE INDEX IF NOT EXISTS idx_crec_staff ON commission_records(staff_id, month);
CREATE INDEX IF NOT EXISTS idx_crec_settled ON commission_records(settled);

-- 让 PostgREST 立即感知新表/新列，无需重启
NOTIFY pgrst, 'reload schema';
