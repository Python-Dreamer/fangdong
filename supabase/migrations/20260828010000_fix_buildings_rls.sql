-- 修复 buildings 表 RLS 策略：改用 auth.uid()，与其他表保持一致
-- 之前用的 current_setting('app.owner_id', true) 在 PostgREST API 请求时未设置，导致插入被拒

DROP POLICY IF EXISTS buildings_owner_all ON buildings;

DROP POLICY IF EXISTS buildings_select_own ON buildings;
CREATE POLICY buildings_select_own ON buildings
  FOR SELECT USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS buildings_insert_own ON buildings;
CREATE POLICY buildings_insert_own ON buildings
  FOR INSERT WITH CHECK (auth.uid() = owner_id);

DROP POLICY IF EXISTS buildings_update_own ON buildings;
CREATE POLICY buildings_update_own ON buildings
  FOR UPDATE USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS buildings_delete_own ON buildings;
CREATE POLICY buildings_delete_own ON buildings
  FOR DELETE USING (auth.uid() = owner_id);

NOTIFY pgrst, 'reload schema';
