# MainProject/dnhelper/database_setup.py

from MainProject.dbhelper.SQLHelper import  SQLHelper


class DatabaseSetup:
    def __init__(self):
        self.db = SQLHelper()

    def setup_all_tables(self):
        """创建所有必要的表"""
        self.create_friendships_table()
        self.create_messages_table()
        self.create_travel_posts_table()
        self.create_post_media_table()
        self.create_post_tags_table()
        self.create_post_interactions_table()
        self.create_user_favorites_table()
        self.create_user_privacy_settings_table()
        print("所有表创建完成")

    def create_friendships_table(self):
        """创建好友关系表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS Friendships \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  user_id \
                  INT \
                  NOT \
                  NULL, \
                  friend_id \
                  INT \
                  NOT \
                  NULL, \
                  status \
                  ENUM \
              ( \
                  'pending', \
                  'accepted', \
                  'blocked' \
              ) DEFAULT 'pending',
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  FOREIGN KEY \
              ( \
                  user_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) \
                                                                ON DELETE CASCADE,
                  FOREIGN KEY \
              ( \
                  friend_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) \
                                                                ON DELETE CASCADE,
                  UNIQUE KEY unique_friendship \
              ( \
                  user_id, \
                  friend_id \
              )
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("Friendships表创建完成")

    def create_messages_table(self):
        """创建聊天消息表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS Messages \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  sender_id \
                  INT \
                  NOT \
                  NULL, \
                  receiver_id \
                  INT \
                  NOT \
                  NULL, \
                  content \
                  TEXT \
                  NOT \
                  NULL, \
                  content_type \
                  ENUM \
              ( \
                  'text', \
                  'image', \
                  'location', \
                  'shared_content' \
              ) DEFAULT 'text',
                  shared_content_id INT,
                  shared_content_type VARCHAR \
              ( \
                  50 \
              ),
                  is_read BOOLEAN DEFAULT FALSE,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY \
              ( \
                  sender_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) ON DELETE CASCADE,
                  FOREIGN KEY \
              ( \
                  receiver_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) \
                ON DELETE CASCADE
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("Messages表创建完成")

    def create_travel_posts_table(self):
        """创建旅行动态表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS TravelPosts \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  user_id \
                  INT \
                  NOT \
                  NULL, \
                  title \
                  VARCHAR \
              ( \
                  100 \
              ),
                  content TEXT NOT NULL,
                  location_name VARCHAR \
              ( \
                  100 \
              ),
                  location_coordinates VARCHAR \
              ( \
                  50 \
              ),
                  privacy_level ENUM \
              ( \
                  'public', \
                  'friends', \
                  'private' \
              ) DEFAULT 'public',
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  view_count INT DEFAULT 0,
                  FOREIGN KEY \
              ( \
                  user_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) \
                                                                ON DELETE CASCADE
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("TravelPosts表创建完成")

    def create_post_media_table(self):
        """创建动态媒体表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS PostMedia \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  post_id \
                  INT \
                  NOT \
                  NULL, \
                  media_type \
                  ENUM \
              ( \
                  'image', \
                  'video' \
              ) NOT NULL,
                  media_url VARCHAR \
              ( \
                  255 \
              ) NOT NULL,
                  thumbnail_url VARCHAR \
              ( \
                  255 \
              ),
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY \
              ( \
                  post_id \
              ) REFERENCES TravelPosts \
              ( \
                  id \
              ) ON DELETE CASCADE
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("PostMedia表创建完成")

    def create_post_tags_table(self):
        """创建动态标签表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS PostTags \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  post_id \
                  INT \
                  NOT \
                  NULL, \
                  tag_name \
                  VARCHAR \
              ( \
                  50 \
              ) NOT NULL,
                  FOREIGN KEY \
              ( \
                  post_id \
              ) REFERENCES TravelPosts \
              ( \
                  id \
              ) ON DELETE CASCADE,
                  UNIQUE KEY unique_post_tag \
              ( \
                  post_id, \
                  tag_name \
              )
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("PostTags表创建完成")

    def create_post_interactions_table(self):
        """创建动态互动表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS PostInteractions \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  post_id \
                  INT \
                  NOT \
                  NULL, \
                  user_id \
                  INT \
                  NOT \
                  NULL, \
                  interaction_type \
                  ENUM \
              ( \
                  'like', \
                  'comment', \
                  'favorite' \
              ) NOT NULL,
                  comment_content TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY \
              ( \
                  post_id \
              ) REFERENCES TravelPosts \
              ( \
                  id \
              ) ON DELETE CASCADE,
                  FOREIGN KEY \
              ( \
                  user_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) \
                ON DELETE CASCADE
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("PostInteractions表创建完成")

    def create_user_favorites_table(self):
        """创建用户收藏表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS UserFavorites \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  user_id \
                  INT \
                  NOT \
                  NULL, \
                  content_id \
                  INT \
                  NOT \
                  NULL, \
                  content_type \
                  VARCHAR \
              ( \
                  50 \
              ) NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY \
              ( \
                  user_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) ON DELETE CASCADE,
                  UNIQUE KEY unique_favorite \
              ( \
                  user_id, \
                  content_id, \
                  content_type \
              )
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("UserFavorites表创建完成")

    def create_user_privacy_settings_table(self):
        """创建用户隐私设置表"""
        sql = '''
              CREATE TABLE IF NOT EXISTS UserPrivacySettings \
              ( \
                  user_id \
                  INT \
                  PRIMARY \
                  KEY, \
                  profile_visibility \
                  ENUM \
              ( \
                  'public', \
                  'friends', \
                  'private' \
              ) DEFAULT 'public',
                  post_default_privacy ENUM \
              ( \
                  'public', \
                  'friends', \
                  'private' \
              ) DEFAULT 'public',
                  allow_friend_requests BOOLEAN DEFAULT TRUE,
                  show_online_status BOOLEAN DEFAULT TRUE,
                  FOREIGN KEY \
              ( \
                  user_id \
              ) REFERENCES Users \
              ( \
                  id \
              ) ON DELETE CASCADE
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
              '''
        self.db.execute(sql)
        print("UserPrivacySettings表创建完成")


if __name__ == '__main__':
    ds = DatabaseSetup()
    ds.setup_all_tables()
