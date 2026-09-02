-- 抄表多表/其他费用明细 + 手工收入流水
-- 1. meter_items：一次抄表可包含多块水表/电表 + 其他费用项（如垃圾费/网费）
--    旧 meter_readings 主表的冷/热/电三行视为第一块表，完全兼容
-- 2. income_records：手工补录收入（历史房租、押金、其他收入）；
--    抄表账单标记"已收取"时系统自动写入 source='meter' 的记录
--    统计口径：收入 = rents.paid(按pay_date) + income_records(按occur_date)

-- ========== 抄表明细表 ==========
CREATE TABLE IF NOT EXISTS meter_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  reading_id UUID REFERENCES meter_readings(id) ON DELETE CASCADE,
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  kind VARCHAR(20) NOT NULL DEFAULT 'electricity', -- electricity/cold_water/hot_water/other
  label VARCHAR(50),                  -- 表名或费用名，如「2号电表」「网费」
  cur_reading NUMERIC,                -- 本期读数（other类为空）
  prev_reading NUMERIC,               -- 上期读数
  usage NUMERIC,                      -- 用量
  price NUMERIC,                      -- 单价
  amount NUMERIC NOT NULL DEFAULT 0,  -- 金额
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE meter_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS meter_items_select_own ON meter_items;
CREATE POLICY meter_items_select_own ON meter_items FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS meter_items_insert_own ON meter_items;
CREATE POLICY meter_items_insert_own ON meter_items FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS meter_items_update_own ON meter_items;
CREATE POLICY meter_items_update_own ON meter_items FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS meter_items_delete_own ON meter_items;
CREATE POLICY meter_items_delete_own ON meter_items FOR DELETE USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON meter_items TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_meter_items_reading ON meter_items(reading_id);
CREATE INDEX IF NOT EXISTS idx_meter_items_owner ON meter_items(owner_id, tenant_id);

-- ========== 收入流水表 ==========
CREATE TABLE IF NOT EXISTS income_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
  tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
  amount NUMERIC NOT NULL DEFAULT 0,
  category VARCHAR(20) NOT NULL DEFAULT 'rent', -- rent=房租, utility=水电, deposit=押金, other=其他
  source VARCHAR(20) NOT NULL DEFAULT 'manual', -- manual=手工录入, meter=抄表已收取自动
  occur_date DATE NOT NULL DEFAULT CURRENT_DATE,
  note TEXT,
  ref_id UUID,                        -- source='meter' 时关联 meter_readings.id
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE income_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS income_rec_select_own ON income_records;
CREATE POLICY income_rec_select_own ON income_records FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS income_rec_insert_own ON income_records;
CREATE POLICY income_rec_insert_own ON income_records FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS income_rec_update_own ON income_records;
CREATE POLICY income_rec_update_own ON income_records FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS income_rec_delete_own ON income_records;
CREATE POLICY income_rec_delete_own ON income_records FOR DELETE USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON income_records TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_income_rec_owner_date ON income_records(owner_id, occur_date);
CREATE INDEX IF NOT EXISTS idx_income_rec_ref ON income_records(ref_id);

NOTIFY pgrst, 'reload schema';
