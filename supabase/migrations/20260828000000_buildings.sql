-- 公寓/楼栋表
CREATE TABLE IF NOT EXISTS buildings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL,
  name VARCHAR(100) NOT NULL,
  address TEXT,
  notes TEXT,
  cold_water_price NUMERIC DEFAULT 5,
  hot_water_price NUMERIC DEFAULT 6,
  electricity_price NUMERIC DEFAULT 1.5,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE buildings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS buildings_owner_all ON buildings;
CREATE POLICY buildings_owner_all ON buildings
  FOR ALL
  USING (owner_id = current_setting('app.owner_id', true)::uuid)
  WITH CHECK (owner_id = current_setting('app.owner_id', true)::uuid);

GRANT SELECT, INSERT, UPDATE, DELETE ON buildings TO anon, authenticated;

-- rooms 表加 building_id
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS building_id UUID REFERENCES buildings(id) ON DELETE SET NULL;

-- 根据现有 address 自动创建公寓并关联
DO $$
DECLARE
  r RECORD;
  bid UUID;
  bname TEXT;
  existing_bid UUID;
BEGIN
  FOR r IN SELECT DISTINCT address, owner_id FROM rooms WHERE address IS NOT NULL AND address != '' LOOP
    -- 规范化名称：去掉"公寓"后缀做模糊匹配
    bname := TRIM(r.address);
    
    -- 查找是否已有同名公寓
    SELECT id INTO existing_bid FROM buildings 
    WHERE owner_id = r.owner_id AND name = bname LIMIT 1;
    
    IF existing_bid IS NULL THEN
      -- 也检查是否有包含关系的（如"祥和"匹配"祥和公寓"）
      SELECT id INTO existing_bid FROM buildings 
      WHERE owner_id = r.owner_id AND (
        name LIKE bname || '%' OR bname LIKE name || '%'
      ) LIMIT 1;
    END IF;
    
    IF existing_bid IS NULL THEN
      INSERT INTO buildings (owner_id, name, address) 
      VALUES (r.owner_id, bname, r.address)
      RETURNING id INTO bid;
    ELSE
      bid := existing_bid;
    END IF;
    
    -- 更新该 address 下的所有房间
    UPDATE rooms SET building_id = bid 
    WHERE owner_id = r.owner_id AND address = r.address AND building_id IS NULL;
  END LOOP;
END $$;

-- 刷新 PostgREST schema cache
NOTIFY pgrst, 'reload schema';
