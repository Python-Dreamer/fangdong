-- ============================================================
-- v59: 历史已收取抄表账单补记收入（幂等，可重复执行）
-- 只处理 income_records 中尚不存在对应 source='meter' 记录的已收账单
-- ============================================================

INSERT INTO income_records (owner_id, room_id, tenant_id, amount, category, source, occur_date, note, ref_id, created_at)
SELECT
  m.owner_id,
  m.room_id,
  m.tenant_id,
  COALESCE(m.total_fee, 0),
  'utility',
  'meter',
  COALESCE(m.paid_date, m.reading_date, CURRENT_DATE),
  '历史抄表已收取补记',
  m.id,
  now()
FROM meter_readings m
WHERE m.paid = true
  AND COALESCE(m.total_fee, 0) > 0
  AND NOT EXISTS (
    SELECT 1 FROM income_records ir
    WHERE ir.source = 'meter' AND ir.ref_id = m.id
  );

-- 通知 PostgREST 刷新 schema 缓存
NOTIFY pgrst, 'reload schema';
