-- 睡眠模块表名前缀迁移 (sleep_)
-- 执行前请备份数据库

RENAME TABLE user_status      TO sleep_user_status;
RENAME TABLE friendship       TO sleep_friendship;
RENAME TABLE user_profile     TO sleep_user_profile;
RENAME TABLE app_config       TO sleep_app_config;
RENAME TABLE upload_session   TO sleep_upload_session;
RENAME TABLE user_oss_files   TO sleep_user_oss_files;
RENAME TABLE system_material   TO sleep_system_material;
