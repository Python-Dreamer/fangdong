-- 维护支出 + 租金调整提醒
-- 1. expenses：房屋维护/公共支出记录，按 expense_date 归属月份，从月度收入中扣除
-- 2. rent_adjustments：未来租金调整计划（涨/降），到期前7天起每日提醒，到期后可标记已处理

-- ========== 支出表 ==========
CREATE TABLE IF NOT EXISTS expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
  amount NUMERIC NOT NULL DEFAULT 0,
  category VARCHAR(20) NOT NULL DEFAULT 'maintenance', -- maintenance=维修, utility=水电, other=其他
  expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS expenses_select_own ON expenses;
CREATE POLICY expenses_select_own ON expenses FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS expenses_insert_own ON expenses;
CREATE POLICY expenses_insert_own ON expenses FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS expenses_update_own ON expenses;
CREATE POLICY expenses_update_own ON expenses FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS expenses_delete_own ON expenses;
CREATE POLICY expenses_delete_own ON expenses FOR DELETE USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON expenses TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_expenses_owner_date ON expenses(owner_id, expense_date);

-- ========== 租金调整计划表 ==========
CREATE TABLE IF NOT EXISTS rent_adjustments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  adjust_date DATE NOT NULL,              -- 生效日期
  direction VARCHAR(10) NOT NULL,         -- increase=涨租, decrease=降租
  amount NUMERIC NOT NULL DEFAULT 0,      -- 变动金额（正数）
  note TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending=待处理, done=已处理
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE rent_adjustments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rent_adj_select_own ON rent_adjustments;
CREATE POLICY rent_adj_select_own ON rent_adjustments FOR SELECT USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS rent_adj_insert_own ON rent_adjustments;
CREATE POLICY rent_adj_insert_own ON rent_adjustments FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS rent_adj_update_own ON rent_adjustments;
CREATE POLICY rent_adj_update_own ON rent_adjustments FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS rent_adj_delete_own ON rent_adjustments;
CREATE POLICY rent_adj_delete_own ON rent_adjustments FOR DELETE USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON rent_adjustments TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_rent_adj_owner_status ON rent_adjustments(owner_id, status, adjust_date);

NOTIFY pgrst, 'reload schema';
