-- ================================================
-- 瑞丽找房 - 服务市场模块 数据库脚本
-- 执行方式：Supabase Dashboard → SQL Editor → New query → Run
-- ================================================

-- 1. 服务类型表
CREATE TABLE IF NOT EXISTS service_types (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT DEFAULT '🔧',
  sort_order INT DEFAULT 0,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 服务方表（家政阿姨、维修师傅等）
CREATE TABLE IF NOT EXISTS service_providers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  type_ids UUID[] DEFAULT '{}',
  service_area TEXT,
  price_hint TEXT,
  description TEXT,
  photo_url TEXT,
  rating_avg NUMERIC(3,2) DEFAULT 0,
  rating_count INT DEFAULT 0,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 服务订单表
CREATE TABLE IF NOT EXISTS service_orders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID NOT NULL,
  provider_id UUID NOT NULL REFERENCES service_providers(id) ON DELETE CASCADE,
  tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
  room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
  service_type TEXT,
  service_date TEXT,
  status TEXT DEFAULT 'pending',
  amount NUMERIC(10,2),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 服务评价表
CREATE TABLE IF NOT EXISTS service_reviews (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES service_orders(id) ON DELETE CASCADE,
  provider_id UUID NOT NULL REFERENCES service_providers(id) ON DELETE CASCADE,
  user_name TEXT,
  rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- RLS 策略
-- ================================================

ALTER TABLE service_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_reviews ENABLE ROW LEVEL SECURITY;

-- service_types: 所有人可读
CREATE POLICY "service_types_public_read" ON service_types
  FOR SELECT USING (true);
-- 仅认证用户可写（管理员后续手动添加类型）
CREATE POLICY "service_types_auth_write" ON service_types
  FOR ALL USING (auth.role() = 'authenticated');

-- service_providers: 所有人可读，拥有者可管理
CREATE POLICY "service_providers_public_read" ON service_providers
  FOR SELECT USING (true);
CREATE POLICY "service_providers_owner_manage" ON service_providers
  FOR ALL USING (auth.uid() = owner_id);

-- service_orders: 拥有者可管理
CREATE POLICY "service_orders_owner_manage" ON service_orders
  FOR ALL USING (auth.uid() = owner_id);

-- service_reviews: 所有人可读，认证用户可写
CREATE POLICY "service_reviews_public_read" ON service_reviews
  FOR SELECT USING (true);
CREATE POLICY "service_reviews_auth_write" ON service_reviews
  FOR ALL USING (auth.role() = 'authenticated');

-- ================================================
-- 预置服务类型（家政相关）
-- ================================================

INSERT INTO service_types (name, icon, sort_order) VALUES
  ('家政保洁', '🧹', 1),
  ('房屋维修', '🔧', 2),
  ('搬家服务', '🚚', 3),
  ('换锁开锁', '🔑', 4),
  ('家电清洗', '🧊', 5),
  ('管道疏通', '🪠', 6),
  ('除虫灭害', '🐜', 7),
  ('空调维修', '❄️', 8);

-- ================================================
-- 索引（提升查询性能）
-- ================================================

CREATE INDEX IF NOT EXISTS idx_service_providers_owner ON service_providers(owner_id);
CREATE INDEX IF NOT EXISTS idx_service_providers_active ON service_providers(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_service_orders_provider ON service_orders(provider_id);
CREATE INDEX IF NOT EXISTS idx_service_orders_status ON service_orders(status);
CREATE INDEX IF NOT EXISTS idx_service_reviews_provider ON service_reviews(provider_id);
