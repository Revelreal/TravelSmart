# SmartTravel 服务器端部署完整指南

## 📋 项目概述

SmartTravel 是一个 AI 旅行推荐系统，采用分布式架构设计，包含：

- **后端**: FastAPI + Python
- **数据库**: MySQL + MongoDB + Redis
- **代理**: Nginx 反向代理
- **容器化**: Docker + Docker Compose
- **域名**: 支持自定义域名和 SSL 证书

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│        Nginx (反向代理/SSL)          │
├─────────────────────────────────────┤
│     FastAPI (Python 后端 API)       │
├─────────────────────────────────────┤
│  MySQL + MongoDB + Redis (数据层)    │
└─────────────────────────────────────┘
```

## 📝 环境要求

- **操作系统**: Ubuntu 20.04+ LTS
- **内存**: 最少 2GB，推荐 4GB+
- **硬盘**: 最少 20GB 可用空间
- **网络**: 公网 IP 和已备案域名（可选）
- **权限**: sudo 管理员权限

## 🚀 部署步骤

### 第一步：系统环境准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim htop tree unzip python3-venv python3-dev python3-pip

# 创建项目目录结构
sudo mkdir -p /opt/smarttravel/{config,logs,data,plugins,scripts,backend}
sudo mkdir -p /var/smarttravel/{uploads,cache,plugins,static}

# 创建专用用户
sudo useradd -r -s /bin/bash smarttravel

# 设置目录权限
sudo chown -R smarttravel:smarttravel /opt/smarttravel
sudo chown -R smarttravel:smarttravel /var/smarttravel
```

### 第二步：Docker 和数据库部署

#### 安装 Docker

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install -y docker-compose

# 将用户添加到 docker 组
sudo usermod -aG docker smarttravel
```

#### 创建 Docker Compose 配置

```bash
cd /opt/smarttravel

# 创建 docker-compose.yml
sudo -u smarttravel tee docker-compose.yml > /dev/null << 'EOF'
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: smarttravel_mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: SmartTravel2024!
      MYSQL_DATABASE: smarttravel
      MYSQL_USER: smarttravel_user
      MYSQL_PASSWORD: ST_mysql_2024!
    ports:
      - "3307:3306"  # 避免端口冲突，使用 3307
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - smarttravel_network

  mongodb:
    image: mongo:6.0
    container_name: smarttravel_mongo
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: smarttravel_admin
      MONGO_INITDB_ROOT_PASSWORD: ST_mongo_2024!
      MONGO_INITDB_DATABASE: smarttravel_sessions
    ports:
      - "27018:27017"  # 避免端口冲突，使用 27018
    volumes:
      - mongo_data:/data/db
    networks:
      - smarttravel_network

  redis:
    image: redis:7-alpine
    container_name: smarttravel_redis
    restart: always
    command: redis-server --requirepass ST_redis_2024!
    ports:
      - "6380:6379"  # 避免端口冲突，使用 6380
    volumes:
      - redis_data:/data
    networks:
      - smarttravel_network

volumes:
  mysql_data:
  mongo_data:
  redis_data:

networks:
  smarttravel_network:
    driver: bridge
EOF

# 启动数据库服务
sudo -u smarttravel docker-compose up -d
```

#### 初始化数据库

**MySQL 表结构初始化：**

```bash
# 创建 MySQL 初始化脚本
sudo -u smarttravel tee config/init_mysql.sql > /dev/null << 'EOF'
USE smarttravel;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    subscription_tier ENUM('free', 'premium', 'enterprise') DEFAULT 'free'
);

-- 会话表
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    session_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 插件管理表
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    author VARCHAR(50),
    description TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    download_url VARCHAR(255),
    file_size INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL
);

-- 用户插件关联表
CREATE TABLE IF NOT EXISTS user_plugins (
    user_id INT,
    plugin_id VARCHAR(50),
    installed_version VARCHAR(20),
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, plugin_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_updated ON sessions(updated_at);
CREATE INDEX idx_plugins_status ON plugins(status);

-- 插入示例数据
INSERT IGNORE INTO plugins (plugin_id, name, version, author, description, status) VALUES
('weather-plugin', '天气查询插件', '1.0.0', 'SmartTravel Team', '提供目的地天气信息查询', 'approved'),
('translate-plugin', '翻译助手插件', '1.0.0', 'SmartTravel Team', '多语言翻译支持', 'approved'),
('maps-plugin', '地图导航插件', '1.0.0', 'SmartTravel Team', '地图导航和路线规划', 'approved');
EOF

# 执行初始化
docker exec -i smarttravel_mysql mysql -u root -pSmartTravel2024! < config/init_mysql.sql
```

**MongoDB 集合初始化：**

```bash
# 创建 MongoDB 初始化脚本
sudo -u smarttravel tee config/init_mongodb.js > /dev/null << 'EOF'
db = db.getSiblingDB('smarttravel_sessions');

// 创建集合
db.createCollection('session_messages');
db.createCollection('plugin_data');
db.createCollection('user_cache');

// 创建索引
db.session_messages.createIndex({ "session_id": 1 });
db.session_messages.createIndex({ "session_id": 1, "messages.timestamp": -1 });
db.plugin_data.createIndex({ "plugin_id": 1, "user_id": 1 });
db.user_cache.createIndex({ "user_id": 1 });

// 插入示例数据
db.session_messages.insertOne({
    session_id: "demo_session_001",
    created_at: new Date(),
    messages: [
        {
            message_id: "msg_001",
            role: "user",
            content: "帮我规划一下北京3日游",
            timestamp: new Date(),
            attachments: []
        }
    ],
    metadata: {
        destination: "北京",
        travel_dates: ["2024-06-01", "2024-06-03"],
        preferences: ["历史文化", "美食"]
    }
});
EOF

# 执行初始化
docker exec -i smarttravel_mongo mongosh --host localhost --username smarttravel_admin --password ST_mongo_2024! < config/init_mongodb.js
```

### 第三步：Python 后端应用

#### 创建虚拟环境和安装依赖

```bash
cd /opt/smarttravel/backend

# 创建虚拟环境
sudo -u smarttravel python3 -m venv venv

# 创建 requirements.txt
sudo -u smarttravel tee requirements.txt > /dev/null << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymongo==4.6.0
redis==5.0.1
pydantic==2.5.0
python-dotenv==1.0.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
mysql-connector-python==8.2.0
aiofiles==23.2.1
python-multipart==0.0.6
Pillow==10.1.0
EOF

# 使用清华源安装依赖（加速下载）
sudo -u smarttravel bash -c "source venv/bin/activate && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
```

#### 创建数据库连接工具

```bash
# 创建 utils/database.py
sudo -u smarttravel mkdir -p utils
sudo -u smarttravel tee utils/database.py > /dev/null << 'EOF'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pymongo import MongoClient
import redis

# 配置类
class Config:
    mysql_host = "localhost"
    mysql_port = 3307
    mysql_database = "smarttravel"
    mysql_user = "smarttravel_user"
    mysql_password = "ST_mysql_2024!"
    
    mongodb_host = "localhost"
    mongodb_port = 27018
    mongodb_database = "smarttravel_sessions"
    mongodb_user = "smarttravel_admin"
    mongodb_password = "ST_mongo_2024!"
    
    redis_host = "localhost"
    redis_port = 6380
    redis_password = "ST_redis_2024!"
    redis_db = 0

settings = Config()

# MySQL 连接
MYSQL_URL = f"mysql+mysqlconnector://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
engine = create_engine(MYSQL_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB 连接
mongodb_client = MongoClient(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    username=settings.mongodb_user,
    password=settings.mongodb_password,
    authSource='admin'
)
mongodb_db = mongodb_client[settings.mongodb_database]

# Redis 连接
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True
)

# 测试数据库连接
async def test_connections():
    success = True
    try:
        # 测试 MySQL
        db = SessionLocal()
        result = db.execute(text("SELECT 1 as test"))
        db.close()
        print("✅ MySQL连接成功")
        
        # 测试 MongoDB
        collections = mongodb_db.list_collection_names()
        print("✅ MongoDB连接成功")
        
        # 测试 Redis
        redis_client.ping()
        print("✅ Redis连接成功")
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        success = False
    
    return success
EOF
```

#### 创建 FastAPI 主应用

```bash
# 创建 main.py
sudo -u smarttravel tee main.py > /dev/null << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from utils.database import test_connections

# 应用配置
APP_NAME = "SmartTravel API"
VERSION = "1.0.0"
HOST = "0.0.0.0"
PORT = 8000

# 创建 FastAPI 应用
app = FastAPI(
    title=APP_NAME,
    description="AI旅行推荐系统API",
    version=VERSION
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("🚀 SmartTravel API 正在启动...")
    connection_ok = await test_connections()
    if connection_ok:
        print("✅ 所有数据库连接正常")

@app.get("/")
async def root():
    return {
        "message": "欢迎使用SmartTravel API",
        "version": VERSION,
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": VERSION
    }

@app.get("/api/test")
async def test_endpoint():
    try:
        connection_ok = await test_connections()
        return {
            "database_status": "all_connected" if connection_ok else "partial_connection",
            "message": "API测试成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@app.get("/api/info")
async def app_info():
    return {
        "app_name": APP_NAME,
        "version": VERSION,
        "features": ["用户认证", "会话管理", "插件系统", "AI旅行推荐"],
        "databases": ["MySQL", "MongoDB", "Redis"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
EOF

# 启动 FastAPI 应用
sudo -u smarttravel bash -c "cd /opt/smarttravel/backend && source venv/bin/activate && nohup python main.py > ../logs/api.log 2>&1 &"
```

### 第四步：Nginx 反向代理配置

#### 配置防火墙

```bash
# 配置防火墙规则
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8000       # 禁止外部直接访问 FastAPI
sudo ufw allow from 127.0.0.1 to any port 8000  # 允许本地访问
```

#### 创建 Nginx 配置

```bash
# 创建 Nginx 配置文件
sudo tee /opt/smarttravel/config/nginx/smarttravel > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # 替换为你的域名
    
    access_log /opt/smarttravel/logs/nginx_access.log;
    error_log /opt/smarttravel/logs/nginx_error.log;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/smarttravel/static/;
        expires 1y;
    }
    
    location /plugins/ {
        alias /var/smarttravel/plugins/;
    }
}
EOF

# 启用配置
sudo rm -f /etc/nginx/sites-enabled/default  # 删除默认配置
sudo ln -sf /opt/smarttravel/config/nginx/smarttravel /etc/nginx/sites-available/smarttravel
sudo ln -sf /etc/nginx/sites-available/smarttravel /etc/nginx/sites-enabled/smarttravel

# 测试并启动 Nginx
sudo nginx -t && sudo systemctl start nginx
```

### 第五步：域名和 SSL 配置（可选）

#### 配置域名解析

确保你的域名 A 记录指向服务器 IP 地址。

#### 获取 SSL 证书

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com --email admin@your-domain.com --agree-tos --non-interactive

# 设置自动续期
sudo certbot renew --dry-run
```

## 🚨 常见问题及解决方案

### 1. 端口冲突问题

**问题**: 80 端口被占用，Nginx 无法启动

```bash
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
```

**解决方案**:

```bash
# 查找占用 80 端口的进程
sudo netstat -tulpn | grep :80

# 停止占用端口的服务（如 Docker 容器）
docker stop container_name

# 或者修改 Nginx 配置使用其他端口
listen 8080;  # 在 Nginx 配置中
```

### 2. Docker 权限问题

**问题**: smarttravel 用户无法访问 Docker

```bash
PermissionError: [Errno 13] Permission denied
```

**解决方案**:

```bash
# 将用户添加到 docker 组
sudo usermod -aG docker smarttravel

# 重启 Docker 服务
sudo systemctl restart docker
```

### 3. Python 虚拟环境创建失败

**问题**: `python3-venv` 包未安装

```bash
The virtual environment was not created successfully because ensurepip is not available
```

**解决方案**:

```bash
# 安装必要的 Python 包
sudo apt install -y python3-venv python3-dev python3-pip
```

### 4. Nginx 配置语法错误

**问题**: `add_header` 指令位置错误

```bash
nginx: [emerg] "add_header" directive is not allowed here
```

**解决方案**:

```bash
# 确保 add_header 指令在正确的 location 块内
location / {
    add_header Access-Control-Allow-Origin "*" always;
    proxy_pass http://127.0.0.1:8000;
}
```

### 5. 数据库连接失败

**问题**: 无法连接到数据库

**解决方案**:

```bash
# 检查容器状态
docker ps

# 检查容器日志
docker logs smarttravel_mysql
docker logs smarttravel_mongo
docker logs smarttravel_redis

# 重启数据库容器
docker-compose restart mysql mongodb redis
```

## 🔧 管理和维护

### 服务管理脚本

```bash
# 创建服务管理脚本
sudo tee /opt/smarttravel/scripts/manage_services.sh > /dev/null << 'EOF'
#!/bin/bash
case "$1" in
    start)
        echo "🚀 启动SmartTravel服务..."
        sudo systemctl start nginx
        docker-compose -f /opt/smarttravel/docker-compose.yml up -d
        sudo -u smarttravel bash -c "cd /opt/smarttravel/backend && source venv/bin/activate && nohup python main.py > ../logs/api.log 2>&1 &"
        ;;
    stop)
        echo "🛑 停止SmartTravel服务..."
        sudo pkill -f "python main.py"
        docker-compose -f /opt/smarttravel/docker-compose.yml down
        sudo systemctl stop nginx
        ;;
    restart)
        $0 stop && sleep 3 && $0 start
        ;;
    status)
        echo "Nginx: $(systemctl is-active nginx)"
        echo "FastAPI: $(pgrep -f 'python main.py' > /dev/null && echo '运行中' || echo '未运行')"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep smarttravel
        ;;
esac
EOF

chmod +x /opt/smarttravel/scripts/manage_services.sh
```

### 日志管理

```bash
# 查看应用日志
tail -f /opt/smarttravel/logs/api.log

# 查看 Nginx 日志
tail -f /opt/smarttravel/logs/nginx_access.log
tail -f /opt/smarttravel/logs/nginx_error.log

# 查看数据库日志
docker logs smarttravel_mysql
docker logs smarttravel_mongo
docker logs smarttravel_redis
```

### 备份和恢复

```bash
# 数据库备份
docker exec smarttravel_mysql mysqldump -u root -pSmartTravel2024! smarttravel > backup_mysql.sql
docker exec smarttravel_mongo mongodump --host localhost --username smarttravel_admin --password ST_mongo_2024! --out /backup

# 配置文件备份
tar -czf smarttravel_config_backup.tar.gz /opt/smarttravel/config
```

## 📊 性能优化建议

1. **数据库优化**
   - 配置 MySQL 连接池
   - 设置 Redis 内存限制
   - 优化 MongoDB 索引
2. **Nginx 优化**
   - 启用 gzip 压缩
   - 配置静态文件缓存
   - 调整 worker 进程数
3. **应用优化**
   - 使用异步数据库连接
   - 实现 API 缓存
   - 配置日志轮转

## 📈 监控和报警

### 系统监控

```bash
# 系统资源监控
htop
df -h
free -h

# 服务状态检查
systemctl status nginx
docker stats
```

### API 监控

```bash
# API 健康检查
curl https://your-domain.com/api/health

# 性能测试
ab -n 1000 -c 10 https://your-domain.com/api/health
```

## 🔐 安全配置

1. **防火墙配置**
   - 只开放必要端口 (80, 443, 22)
   - 限制数据库端口访问
2. **SSL/TLS 配置**
   - 使用 Let's Encrypt 免费证书
   - 配置 HSTS 头部
   - 禁用不安全的 SSL 协议
3. **应用安全**
   - 使用强密码
   - 定期更新依赖包
   - 配置 CORS 策略

## 📝 总结

通过以上步骤，你应该能够成功部署 SmartTravel 服务器端应用。关键要点：

- **分层架构**: 数据库层 → API 层 → 代理层
- **容器化**: 使用 Docker 管理数据库服务
- **代理配置**: Nginx 提供反向代理和 SSL 终止
- **安全性**: 防火墙、SSL 证书、权限控制
- **可维护性**: 服务管理脚本、日志监控、备份策略

部署完成后，你可以通过以下地址访问服务：

- **主页**: https://your-domain.com
- **API 文档**: https://your-domain.com/docs
- **健康检查**: https://your-domain.com/api/health

接下来可以开始开发客户端应用和扩展功能模块。