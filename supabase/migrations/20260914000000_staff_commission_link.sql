-- v86 需求3：员工提成与租户缴费记录联动（纯增量：仅新增2条员工只读RLS策略，不改任何既有策略/表）
-- 执行方式：在服务器 sudo docker exec -i fd_db psql -U postgres -d postgres < 本文件
-- 幂等：可重复执行（DROP POLICY IF EXISTS）
-- 安全模型：员工此前只能读 rooms/buildings/自己的提成；本文件仅放开【与本人提成记录相关】的
--   租户行(tenants)与账单行(rents)，看不到其他租客、看不到账本全貌。限定路径：
--   必须存在一条 commission_records，其 staff_id = 当前登录员工、tenant_id 指向该行、owner_id 一致。

-- ========== 员工只读：与本人提成相关的租户（姓名/房号等，用于提成对账展示）==========
DROP POLICY IF EXISTS tenants_select_staff_comm ON tenants;
CREATE POLICY tenants_select_staff_comm ON tenants FOR SELECT
  USING (
    auth.uid() = owner_id
    OR EXISTS (
      SELECT 1 FROM commission_records cr
      JOIN staff_accounts sa ON sa.id = auth.uid() AND sa.active
      WHERE cr.tenant_id = tenants.id
        AND cr.staff_id = sa.staff_id
        AND cr.owner_id = sa.owner_id
        AND cr.owner_id = tenants.owner_id
    )
  );

-- ========== 员工只读：与本人提成相关租户的缴费账单（缴费状态/实收，用于核对按实收提成）==========
DROP POLICY IF EXISTS rents_select_staff_comm ON rents;
CREATE POLICY rents_select_staff_comm ON rents FOR SELECT
  USING (
    auth.uid() = owner_id
    OR EXISTS (
      SELECT 1 FROM commission_records cr
      JOIN staff_accounts sa ON sa.id = auth.uid() AND sa.active
      WHERE cr.tenant_id = rents.tenant_id
        AND cr.staff_id = sa.staff_id
        AND cr.owner_id = sa.owner_id
        AND cr.owner_id = rents.owner_id
    )
  );

NOTIFY pgrst, 'reload schema';
