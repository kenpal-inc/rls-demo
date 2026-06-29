SELECT
  -- テーブル名
  c.relname,
  -- RLS有効フラグ
  c.relrowsecurity,
  -- RLS強制フラグ
  c.relforcerowsecurity,
  -- ポリシー数
  (
    SELECT COUNT(*)
    FROM pg_policy p
    WHERE p.polrelid = c.oid
  ) AS policy_count
FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE
  -- 通常テーブルのみ（view 等を除外）
  c.relkind = 'r'
  -- public スキーマのみ
  AND n.nspname = 'public'
  -- company_seq カラムを持つテーブルのみ
  AND EXISTS (
    SELECT 1
    FROM pg_attribute a
    WHERE a.attrelid = c.oid
      AND a.attname = 'company_seq'
      AND NOT a.attisdropped
  )
  -- 条件を満たさないテーブルを抽出
  -- RLSが有効でない、または強制されていない、またはポリシーが1つも定義されていない
  AND (
    NOT c.relrowsecurity
    OR NOT c.relforcerowsecurity
    OR (
      SELECT COUNT(*)
      FROM pg_policy p
      WHERE p.polrelid = c.oid
    ) = 0
  );