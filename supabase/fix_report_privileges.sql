-- ============================================================
-- 修复举报功能：确保 service_role 对 listing_reports 有写权限
-- 自适应：无论自建库角色是否已创建，执行后即可正常提交举报
-- 幂等，可重复执行
-- ============================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END $$;

-- PostgREST 用登录角色连接后，需要能 SET ROLE 到 service_role
DO $$
DECLARE r text;
BEGIN
  FOR r IN SELECT rolname FROM pg_roles
           WHERE rolname IN ('authenticator','postgres','root') LOOP
    EXECUTE format('GRANT service_role TO %I', r);
  END LOOP;
END $$;

-- 表级全部权限（RLS 由策略控制；service_role 通常 BYPASSRLS）
GRANT SELECT, INSERT, UPDATE, DELETE ON public.listing_reports TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO service_role;

-- 通知 PostgREST 重载结构缓存（函数存在时）
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'postgrest_ddl_hook') THEN
    PERFORM public.postgrest_ddl_hook();
  END IF;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;
