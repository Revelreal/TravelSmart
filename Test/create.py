# MainProject/database/migrations/create_user_view_history.py

def migrate_up(db_helper):
    """创建 UserViewHistory 表"""
    sql = """
          CREATE TABLE IF NOT EXISTS UserViewHistory \
          ( \
              id \
              INT \
              AUTO_INCREMENT \
              PRIMARY \
              KEY \
              COMMENT \
              '主键ID', \
              user_id \
              INT \
              NOT \
              NULL \
              COMMENT \
              '查看用户ID', \
              content_id \
              INT \
              NOT \
              NULL \
              COMMENT \
              '内容ID（如动态ID）', \
              content_type \
              VARCHAR \
          ( \
              20 \
          ) NOT NULL DEFAULT 'post' COMMENT '内容类型',
              view_count INT NOT NULL DEFAULT 1 COMMENT '查看次数',
              first_viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '首次查看时间',
              last_viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后查看时间',
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
              updated_at DATETIME DEFAULT CURRENT_TIMESTAMP \
                                                                ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间', \
              INDEX idx_user_id \
          ( \
              user_id \
          ),
              INDEX idx_content \
          ( \
              content_id, \
              content_type \
          ),
              INDEX idx_user_content \
          ( \
              user_id, \
              content_id, \
              content_type \
          ),
              INDEX idx_last_viewed \
          ( \
              last_viewed_at \
          ),
              INDEX idx_content_type \
          ( \
              content_type \
          ), \
              UNIQUE KEY uk_user_content \
          ( \
              user_id, \
              content_id, \
              content_type \
          ),
              FOREIGN KEY \
          ( \
              user_id \
          ) REFERENCES Users \
          ( \
              id \
          ) \
                                                                ON DELETE CASCADE
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci COMMENT='用户查看历史记录表' \
          """

    try:
        db_helper.execute(sql)
        print("UserViewHistory 表创建成功")
        return True
    except Exception as e:
        print(f"创建 UserViewHistory 表失败: {e}")
        return False


def migrate_down(db_helper):
    """删除 UserViewHistory 表"""
    sql = "DROP TABLE IF EXISTS UserViewHistory"

    try:
        db_helper.execute(sql)
        print("UserViewHistory 表删除成功")
        return True
    except Exception as e:
        print(f"删除 UserViewHistory 表失败: {e}")
        return False

if __name__ == '__main__':
    from MainProject.dbhelper.SQLHelper import SQLHelper
    db = SQLHelper()
    migrate_up(db)
