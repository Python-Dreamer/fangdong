-- v81 中介员工子账号（纯增量：1张新表 staff_accounts + 员工只读RLS策略）
-- 执行方式：在服务器 sudo docker exec -i fd_db psql -U postgres -d postgres < 本文件
-- 幂等：可重复执行（IF NOT EXISTS / DROP POLICY IF EXISTS）
-- 安全模型：员工用独立邮箱账号登录；owner_id 指向其老板(=profiles.id/auth.uid)。
--   老板：staff_accounts 全读写(owner_id=自己)；员工：只能读自己那一条(auth.uid=id)。
--   业务表只给员工【只读】策略，且数据严格限定在其老板 owner_id 范围内；
--   员工【看不到】账本/收支/租客隐私/财务/其他员工提成等（不新增策略即被RLS拒绝）。

-- ========== 1. 员工账号关联表 ==========
CREATE TABLE IF NOT EXISTS staff_accounts (
  id UUID PRIMARY KEY,                       -- = 员工的 auth.users.id（登录账号ID）
  owner_id UUID NOT NULL,                    -- 老板的账号ID
  staff_id UUID,                             -- 关联 staff.id（提成/姓名）
  email TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'staff',        -- 固定 'staff'
  active BOOLEAN NOT NULL DEFAULT true,      -- 老板可一键停用
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE staff_accounts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sa_select_own ON staff_accounts;
CREATE POLICY sa_select_own ON staff_accounts FOR SELECT
  USING (auth.uid() = owner_id OR auth.uid() = id);
DROP POLICY IF EXISTS sa_insert_own ON staff_accounts;
CREATE POLICY sa_insert_own ON staff_accounts FOR INSERT
  WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS sa_update_own ON staff_accounts;
CREATE POLICY sa_update_own ON staff_accounts FOR UPDATE
  USING (auth.uid() = owner_id) WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS sa_delete_own ON staff_accounts;
CREATE POLICY sa_delete_own ON staff_accounts FOR DELETE
  USING (auth.uid() = owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON staff_accounts TO anon, authenticated;

CREATE INDEX IF NOT EXISTS idx_sa_owner ON staff_accounts(owner_id, active);
CREATE INDEX IF NOT EXISTS idx_sa_staff ON staff_accounts(staff_id);

-- ========== 2. 员工只读：员工表（员工只能读到自己那条，看不到其他同事）==========
DROP POLICY IF EXISTS staff_select_self ON staff;
CREATE POLICY staff_select_self ON staff FOR SELECT
  USING (
    auth.uid() = owner_id
    OR id = (SELECT sa.staff_id FROM staff_accounts sa WHERE sa.id = auth.uid())
  );

-- ========== 3. 员工只读：提成流水（员工只看自己的提成，且经老板归属校验）==========
DROP POLICY IF EXISTS comm_select_staff ON commission_records;
CREATE POLICY comm_select_staff ON commission_records FOR SELECT
  USING (
    auth.uid() = owner_id
    OR (
      staff_id = (SELECT sa.staff_id FROM staff_accounts sa WHERE sa.id = auth.uid() AND sa.active)
      AND owner_id = (SELECT sa.owner_id FROM staff_accounts sa WHERE sa.id = auth.uid())
    )
  );

-- ========== 4. 员工只读：房源（只看老板名下房源概况，看不到价格/租客隐私字段由前端不展示）==========
DROP POLICY IF EXISTS rooms_select_staff ON rooms;
CREATE POLICY rooms_select_staff ON rooms FOR SELECT
  USING (
    auth.uid() = owner_id
    OR owner_id = (SELECT sa.owner_id FROM staff_accounts sa WHERE sa.id = auth.uid() AND sa.active)
  );

-- ========== 5. 员工只读：楼栋（房源分组名）==========
DROP POLICY IF EXISTS buildings_select_staff ON buildings;
CREATE POLICY buildings_select_staff ON buildings FOR SELECT
  USING (
    auth.uid() = owner_id
    OR owner_id = (SELECT sa.owner_id FROM staff_accounts sa WHERE sa.id = auth.uid() AND sa.active)
  );

-- ========== 6. 更新时间触发器 ==========
DROP TRIGGER IF EXISTS trg_sa_updated ON staff_accounts;
CREATE TRIGGER trg_sa_updated BEFORE UPDATE ON staff_accounts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

NOTIFY pgrst, 'reload schema';
