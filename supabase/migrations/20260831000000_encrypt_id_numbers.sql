-- 身份证号加密存储改造
-- 原理：
--   1. 身份证号以 AES(pgp_sym_encrypt) 加密后存入 id_number，密文前缀 enc:v1:
--   2. 密钥保存在数据库服务器本地文件 /var/lib/postgresql/data/id_enc_key.txt（0600权限，postgres用户只读）
--      密钥不进数据库表、不进数据库备份，拖库只能拿到密文
--   3. 不敏感的派生信息（后4位 id_last4、出生日期 id_birth）明文存储，供列表/详情直接展示
--   4. 同住人 occupants JSONB 内的 id_number 同样加密，并附带 id_last4/id_birth 派生字段
--   5. 编辑回填、Excel导出、电子合同等需要完整号码的场景，调用 decrypt_tenant_ids RPC 解密
--      该函数为 SECURITY DEFINER，内部校验 owner_id = auth.uid()，房东只能解密自己的数据

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ========== 1. 新增派生列 ==========
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS id_last4 VARCHAR(4);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS id_birth DATE;

-- ========== 2. 密钥读取函数（SECURITY DEFINER，从服务器本地文件读密钥） ==========
CREATE OR REPLACE FUNCTION _read_enc_key() RETURNS text AS $$
BEGIN
  RETURN trim(pg_read_file('id_enc_key.txt'));
EXCEPTION WHEN OTHERS THEN
  RAISE EXCEPTION 'encryption key file not readable: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
REVOKE ALL ON FUNCTION _read_enc_key() FROM PUBLIC;

-- ========== 3. 身份证号加密/派生工具函数 ==========
CREATE OR REPLACE FUNCTION _enc_id(plain text) RETURNS text AS $$
BEGIN
  IF plain IS NULL OR plain = '' THEN
    RETURN NULL;
  END IF;
  IF left(plain, 7) = 'enc:v1:' THEN
    RETURN plain;  -- 已加密，避免重复加密
  END IF;
  RETURN 'enc:v1:' || encode(pgp_sym_encrypt(plain, _read_enc_key()), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
REVOKE ALL ON FUNCTION _enc_id(text) FROM PUBLIC;

-- 18位身份证提取出生日期
CREATE OR REPLACE FUNCTION _id_birth_date(plain text) RETURNS date AS $$
BEGIN
  IF plain IS NULL OR length(plain) <> 18 THEN
    RETURN NULL;
  END IF;
  BEGIN
    RETURN (substr(plain,7,4)||'-'||substr(plain,11,2)||'-'||substr(plain,13,2))::date;
  EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ========== 4. 加密触发器（INSERT/UPDATE 自动加密主租客 + 同住人身份证） ==========
CREATE OR REPLACE FUNCTION _encrypt_tenant_ids() RETURNS trigger AS $$
DECLARE
  plain text;
BEGIN
  -- 主租客身份证
  IF NEW.id_number IS NOT NULL AND NEW.id_number <> '' THEN
    plain := NEW.id_number;
    NEW.id_number := _enc_id(plain);
    IF length(plain) = 18 AND left(plain, 7) <> 'enc:v1:' THEN
      NEW.id_last4 := substr(plain, 15, 4);
      NEW.id_birth := _id_birth_date(plain);
    END IF;
  END IF;

  -- 同住人 occupants JSONB 内身份证加密 + 派生字段
  IF NEW.occupants IS NOT NULL AND jsonb_typeof(NEW.occupants) = 'array' THEN
    NEW.occupants := COALESCE((
      SELECT jsonb_agg(
        CASE
          WHEN jsonb_typeof(elem) = 'object'
               AND (elem->>'id_number') IS NOT NULL
               AND (elem->>'id_number') <> ''
               AND left(elem->>'id_number', 7) <> 'enc:v1:'
          THEN
            jsonb_set(
              jsonb_set(
                jsonb_set(
                  elem,
                  '{id_number}',
                  to_jsonb('enc:v1:' || encode(pgp_sym_encrypt(elem->>'id_number', _read_enc_key()), 'base64'))
                ),
                '{id_last4}',
                CASE WHEN length(elem->>'id_number') = 18
                     THEN to_jsonb(substr(elem->>'id_number', 15, 4))
                     ELSE 'null'::jsonb END,
                true
              ),
              '{id_birth}',
              CASE WHEN length(elem->>'id_number') = 18
                     AND _id_birth_date(elem->>'id_number') IS NOT NULL
                   THEN to_jsonb(_id_birth_date(elem->>'id_number')::text)
                   ELSE 'null'::jsonb END,
              true
            )
          ELSE elem
        END
      )
      FROM jsonb_array_elements(NEW.occupants) elem
    ), NEW.occupants);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
REVOKE ALL ON FUNCTION _encrypt_tenant_ids() FROM PUBLIC;

DROP TRIGGER IF EXISTS trg_encrypt_tenant_ids ON tenants;
CREATE TRIGGER trg_encrypt_tenant_ids
  BEFORE INSERT OR UPDATE ON tenants
  FOR EACH ROW EXECUTE FUNCTION _encrypt_tenant_ids();

-- ========== 5. 存量数据加密（一次性迁移） ==========
-- 主租客
UPDATE tenants
SET id_number = _enc_id(id_number),
    id_last4 = CASE WHEN length(id_number) = 18 THEN substr(id_number, 15, 4) ELSE id_last4 END,
    id_birth = CASE WHEN length(id_number) = 18 THEN _id_birth_date(id_number) ELSE id_birth END
WHERE id_number IS NOT NULL
  AND id_number <> ''
  AND left(id_number, 7) <> 'enc:v1:';

-- 同住人
UPDATE tenants t
SET occupants = COALESCE((
  SELECT jsonb_agg(
    CASE
      WHEN jsonb_typeof(elem) = 'object'
           AND (elem->>'id_number') IS NOT NULL
           AND (elem->>'id_number') <> ''
           AND left(elem->>'id_number', 7) <> 'enc:v1:'
      THEN
        jsonb_set(
          jsonb_set(
            jsonb_set(
              elem,
              '{id_number}',
              to_jsonb('enc:v1:' || encode(pgp_sym_encrypt(elem->>'id_number', _read_enc_key()), 'base64'))
            ),
            '{id_last4}',
            CASE WHEN length(elem->>'id_number') = 18
                 THEN to_jsonb(substr(elem->>'id_number', 15, 4))
                 ELSE 'null'::jsonb END,
            true
          ),
          '{id_birth}',
          CASE WHEN length(elem->>'id_number') = 18
                 AND _id_birth_date(elem->>'id_number') IS NOT NULL
               THEN to_jsonb(_id_birth_date(elem->>'id_number')::text)
               ELSE 'null'::jsonb END,
          true
        )
      ELSE elem
    END
  )
  FROM jsonb_array_elements(t.occupants) elem
), t.occupants)
WHERE t.occupants IS NOT NULL
  AND jsonb_typeof(t.occupants) = 'array'
  AND t.occupants::text LIKE '%id_number%';

-- ========== 6. 解密 RPC（仅本人数据，编辑/导出/合同用） ==========
CREATE OR REPLACE FUNCTION decrypt_tenant_ids(p_tenant_ids uuid[])
RETURNS TABLE(id uuid, id_number text, occupants jsonb) AS $$
BEGIN
  RETURN QUERY
  SELECT t.id,
    CASE
      WHEN t.id_number IS NULL THEN NULL
      WHEN left(t.id_number, 7) = 'enc:v1:'
        THEN pgp_sym_decrypt(decode(substr(t.id_number, 8), 'base64'), _read_enc_key())
      ELSE t.id_number
    END AS id_number,
    (
      SELECT jsonb_agg(
        CASE
          WHEN jsonb_typeof(elem) = 'object'
               AND (elem->>'id_number') IS NOT NULL
               AND left(elem->>'id_number', 7) = 'enc:v1:'
          THEN jsonb_set(
                 elem,
                 '{id_number}',
                 to_jsonb(pgp_sym_decrypt(decode(substr(elem->>'id_number', 8), 'base64'), _read_enc_key()))
               )
          ELSE elem
        END
      )
      FROM jsonb_array_elements(COALESCE(t.occupants, '[]'::jsonb)) elem
    ) AS occupants
  FROM tenants t
  WHERE t.id = ANY(p_tenant_ids)
    AND t.owner_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;
REVOKE ALL ON FUNCTION decrypt_tenant_ids(uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION decrypt_tenant_ids(uuid[]) TO anon, authenticated;

-- 刷新 PostgREST schema 缓存
NOTIFY pgrst, 'reload schema';
