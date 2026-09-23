-- v98: workspace_settings 增加收款码路径列（幂等）
ALTER TABLE workspace_settings
  ADD COLUMN IF NOT EXISTS pay_qr_path text DEFAULT '';

-- 确保相关角色可访问该列（与既有权限保持一致）
GRANT SELECT, INSERT, UPDATE, DELETE ON workspace_settings TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON workspace_settings TO authenticator;
