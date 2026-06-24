SELECT schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  -- USING 句
  with_check -- WITH CHECK 句
FROM pg_policies
ORDER BY tablename,
  policyname;