-- 数据库初始化脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 设置时区
ALTER DATABASE delivery_receipt SET timezone TO 'Asia/Shanghai';

-- 创建索引优化查询性能（这些索引应该根据实际使用的查询来调整）
-- 注意：实际的表结构和索引应该通过 Alembic 迁移来管理

-- 设置连接池相关参数
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- 设置日志记录
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 200;

-- 重新加载配置
SELECT pg_reload_conf();