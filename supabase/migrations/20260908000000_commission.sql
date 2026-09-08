-- v76 中介员工提成模块（纯增量：3张新表 + workspace_settings 加开关列）
-- 执行方式：在服务器 docker exec fd_db psql -U postgres -d postgres
-- 幂等：可重复执行（IF NOT EXISTS / DROP POLICY IF EXISTS / ADD COLUMN IF NOT EXISTS）

-- ========== 1. 员工表 ==========
CREATE TABLE IF NOT EXISTS staff (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
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

-- ========== 2. 租约提成配置表（一个租约最多一条，按 tenant_id 唯一）==========
CREATE TABLE IF NOT EXISTS tenant_commission (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  tenant_id UUID NOT NULL UNIQUE,          -- 一个租约一条配置，upsert 用
  staff_id UUID,
  mode VARCHAR(20) NOT NULL DEFAULT 'monthly',   -- monthly=按月计提, onetime=一次性提成
  basis VARCHAR(20) NOT NULL DEFAULT 'effective',-- effective=按租约生效, received=按实收租金
  rate_type VARCHAR(20) NOT NULL DEFAULT 'percent', -- percent=比例%, fixed=固定金额
  rate NUMERIC NOT NULL DEFAULT 0,         -- percent: 百分比数值(如10=10%); fixed: 金额(元)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
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

-- ========== 3. 提成流水表 ==========
CREATE TABLE IF NOT EXISTS commission_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  staff_id UUID,
  tenant_id UUID,
  month VARCHAR(7),                          -- 所属月份 YYYY-MM（一次性=入住月）
  amount NUMERIC NOT NULL DEFAULT 0,         -- 提成金额（元）
  base_amount NUMERIC NOT NULL DEFAULT 0,    -- 计提基数（月租或实收租金）
  mode VARCHAR(20) NOT NULL DEFAULT 'monthly',
  basis VARCHAR(20) NOT NULL DEFAULT 'effective',
  settled BOOLEAN NOT NULL DEFAULT false,    -- 是否已结算
  settled_at TIMESTAMPTZ,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE commission_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS comm_select_own ON commission_records;
CREATE POLICY comm_select_own ON commission_records FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS comm_insert_own ON commission_records;
CREATE POLICY comm_insert_own ON commission_records FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS comm_update_own ON commission_records;
CREATE POLICY comm_update_own ON commission_records FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS comm_delete_own ON commission_records;
CREATE POLICY comm_delete_own ON commission_records FOR DELETE USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON commission_records TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_comm_owner_month ON commission_records(owner_id, month);
CREATE INDEX IF NOT EXISTS idx_comm_staff ON commission_records(staff_id);
CREATE INDEX IF NOT EXISTS idx_comm_settled ON commission_records(owner_id, settled);

-- ========== 4. 设置表加开关列（模块默认关闭）==========
ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS commission_enabled BOOLEAN NOT NULL DEFAULT false;

-- ========== 5. 更新时间触发器（两张带 updated_at 的表）==========
DROP TRIGGER IF EXISTS trg_staff_updated ON staff;
CREATE TRIGGER trg_staff_updated BEFORE UPDATE ON staff
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
DROP TRIGGER IF EXISTS trg_tcomm_updated ON tenant_commission;
CREATE TRIGGER trg_tcomm_updated BEFORE UPDATE ON tenant_commission
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

NOTIFY pgrst, 'reload schema';
