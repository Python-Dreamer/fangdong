-- ================================================
-- 水电抄表模块 数据库脚本
-- 执行方式：在服务器 docker exec fd_db psql -U postgres -d postgres
-- 或 Supabase 自建库的 SQL 控制台
-- ================================================

-- 1. 水电抄表记录表
CREATE TABLE IF NOT EXISTS meter_readings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  room_id UUID,
  reading_date DATE NOT NULL DEFAULT CURRENT_DATE,
  cold_water NUMERIC(10,2),       -- 冷水表累计读数（吨）
  hot_water NUMERIC(10,2),        -- 热水表累计读数（吨）
  electricity NUMERIC(10,2),      -- 电表累计读数（度）
  cold_water_price NUMERIC(10,2), -- 冷水单价（元/吨）
  hot_water_price NUMERIC(10,2),  -- 热水单价（元/吨）
  electricity_price NUMERIC(10,2),-- 电单价（元/度）
  cold_water_usage NUMERIC(10,2), -- 冷水用量（吨，自动算）
  hot_water_usage NUMERIC(10,2),  -- 热水用量
  electricity_usage NUMERIC(10,2),-- 电用量
  cold_water_fee NUMERIC(10,2),   -- 冷水费
  hot_water_fee NUMERIC(10,2),    -- 热水费
  electricity_fee NUMERIC(10,2),  -- 电费
  total_fee NUMERIC(10,2),        -- 合计
  paid BOOLEAN DEFAULT false,     -- 是否已收
  paid_date DATE,                 -- 收款日期
  photo_url TEXT,                 -- 抄表照片（可选）
  notes TEXT,                     -- 备注
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meter_owner ON meter_readings(owner_id);
CREATE INDEX IF NOT EXISTS idx_meter_tenant ON meter_readings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_meter_date ON meter_readings(reading_date);

-- 2. RLS
ALTER TABLE meter_readings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "meter_select_own" ON meter_readings;
CREATE POLICY "meter_select_own" ON meter_readings
  FOR SELECT USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS "meter_insert_own" ON meter_readings;
CREATE POLICY "meter_insert_own" ON meter_readings
  FOR INSERT WITH CHECK (auth.uid() = owner_id);

DROP POLICY IF EXISTS "meter_update_own" ON meter_readings;
CREATE POLICY "meter_update_own" ON meter_readings
  FOR UPDATE USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS "meter_delete_own" ON meter_readings;
CREATE POLICY "meter_delete_own" ON meter_readings
  FOR DELETE USING (auth.uid() = owner_id);

-- 3. 在 rooms 表加默认水电单价（如果房东想按房间配置）
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS cold_water_price NUMERIC(10,2);
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS hot_water_price NUMERIC(10,2);
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS electricity_price NUMERIC(10,2);

-- 4. 在 workspace_settings 加全局默认水电单价
ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS default_cold_water_price NUMERIC(10,2) DEFAULT 5;
ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS default_hot_water_price NUMERIC(10,2) DEFAULT 15;
ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS default_electricity_price NUMERIC(10,2) DEFAULT 1.2;

-- 5. 授权（关键！否则前端anon角色写入会被拒绝）
GRANT SELECT, INSERT, UPDATE, DELETE ON meter_readings TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- 6. 更新已有记录的默认单价（冷5/热6/电1.5）
UPDATE workspace_settings SET default_hot_water_price = 6 WHERE default_hot_water_price = 15;
UPDATE workspace_settings SET default_electricity_price = 1.5 WHERE default_electricity_price = 1.2;
-- 7. 修复已存在的照片路径（去掉重复的contract-photos/前缀）
UPDATE meter_readings SET photo_url = SUBSTRING(photo_url FROM LENGTH('contract-photos/')+1) WHERE photo_url LIKE 'contract-photos/%';
