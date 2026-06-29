SELECT schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  -- USING 句
  qual,
  -- WITH CHECK 句
  with_check
FROM pg_policies
ORDER BY tablename,
  policyname;