#!/bin/bash
# SmartTravel 一键部署脚本
# 使用方法: bash deploy.sh

set -e

DOMAIN="rosmontiscloud.xyz"
PROJECT_DIR="/opt/smarttravel"

echo "🚀 SmartTravel 一键部署开始"
echo "=================================="

# 1. 安装基础环境
echo "📦 安装基础环境..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl

# 2. 创建项目目录
echo "📁 创建项目..."
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. 创建虚拟环境
echo "🐍 创建Python环境..."
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-multipart aiofiles

# 4. 创建主程序
echo "📝 创建应用..."
cat > main.py << 'EOF'
import json, sqlite3, hashlib, uuid, os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# 配置
APP_DIR = Path(__file__).parent
for dir_name in ["data", "static", "files"]:
    (APP_DIR / dir_name).mkdir(exist_ok=True)

DB_PATH = APP_DIR / "data" / "app.db"
active_tokens = {}

app = FastAPI(title="SmartTravel", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/files", StaticFiles(directory="files"), name="files")
security = HTTPBearer()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, 
        password_hash TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY, filename TEXT, original_name TEXT, 
        file_size INTEGER, upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        download_count INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id: int) -> str:
    token = str(uuid.uuid4())
    active_tokens[token] = {
        "user_id": user_id,
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="无效令牌")
    if datetime.now() > active_tokens[token]["expires_at"]:
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="令牌过期")
    return active_tokens[token]

@app.get("/", response_class=HTMLResponse)
async def root():
    return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>SmartTravel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
.container{text-align:center;color:white;max-width:800px;padding:40px}
h1{font-size:4em;margin-bottom:20px;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}
p{font-size:1.3em;margin-bottom:40px;opacity:0.9}
.links{display:flex;gap:20px;justify-content:center;flex-wrap:wrap}
.btn{background:white;color:#667eea;padding:15px 30px;text-decoration:none;border-radius:50px;font-weight:bold;box-shadow:0 10px 30px rgba(0,0,0,0.2);transition:transform 0.3s}
.btn:hover{transform:translateY(-5px)}
.btn.primary{background:#667eea;color:white}
</style></head>
<body>
<div class="container">
<h1>🌍 SmartTravel</h1>
<p>AI智能旅行推荐 • 文件管理 • 云端服务</p>
<div class="links">
<a href="/file-manager" class="btn primary">📁 文件管理</a>
<a href="/docs" class="btn">📚 API文档</a>
<a href="/api/health" class="btn">💚 状态检查</a>
</div>
</div>
</body></html>'''

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "SmartTravel", "domain": "rosmontiscloud.xyz"}

@app.post("/api/auth/register")
async def register(user: UserCreate):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (user.username, user.email, hash_password(user.password)))
        conn.commit()
        user_id = conn.lastrowid
        return {"message": "注册成功", "access_token": generate_token(user_id)}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "用户已存在")
    finally:
        conn.close()

@app.post("/api/auth/login")  
async def login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT id FROM users WHERE username=? AND password_hash=?",
                         (user.username, hash_password(user.password)))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(401, "用户名或密码错误")
    return {"message": "登录成功", "access_token": generate_token(result[0])}

@app.get("/file-manager", response_class=HTMLResponse)
async def file_manager():
    return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>文件管理</title>
<style>
body{font-family:Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5}
.container{max-width:1000px;margin:0 auto}
.header{background:white;padding:30px;border-radius:10px;margin-bottom:20px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.upload-area{background:white;border:3px dashed #007bff;padding:50px;text-align:center;border-radius:10px;margin-bottom:20px;cursor:pointer;transition:all 0.3s}
.upload-area:hover{border-color:#0056b3;background:#f8f9ff}
.file-list{background:white;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.file-item{display:flex;align-items:center;padding:20px;border-bottom:1px solid #eee}
.file-item:hover{background:#f8f9fa}
.file-info{flex-grow:1;margin-left:15px}
.btn{background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;margin-left:10px}
.btn:hover{background:#0056b3}
</style></head>
<body>
<div class="container">
<div class="header">
<h1>📁 文件管理中心</h1>
<p>拖拽或点击上传文件，支持在线预览和分享</p>
</div>
<div class="upload-area" onclick="document.getElementById('file').click()">
<h2>📤 点击或拖拽上传文件</h2>
<p>支持任意文件类型，最大100MB</p>
<input type="file" id="file" multiple style="display:none" onchange="upload()">
</div>
<div class="file-list" id="files">正在加载...</div>
</div>
<script>
async function loadFiles(){
try{
const r=await fetch('/api/files');
const d=await r.json();
document.getElementById('files').innerHTML=d.files.length?d.files.map(f=>`
<div class="file-item">
<div style="font-size:30px">📄</div>
<div class="file-info">
<div style="font-weight:bold">${f.original_name}</div>
<div style="color:#666">${(f.file_size/1024).toFixed(1)}KB • ${new Date(f.upload_time).toLocaleString()}</div>
</div>
<a href="/files/${f.filename}" class="btn" target="_blank">预览</a>
<a href="/files/${f.filename}" class="btn" download>下载</a>
</div>`).join(''):'<div style="text-align:center;padding:40px;color:#666">暂无文件</div>';
}catch(e){document.getElementById('files').innerHTML='<div style="text-align:center;padding:40px;color:red">加载失败</div>'}}

async function upload(){
const files=document.getElementById('file').files;
for(let file of files){
const fd=new FormData();
fd.append('file',file);
try{
const r=await fetch('/api/upload',{method:'POST',body:fd});
if(r.ok)console.log('上传成功:',file.name);
else console.log('上传失败:',file.name);
}catch(e){console.log('上传错误:',e)}}
document.getElementById('file').value='';
setTimeout(loadFiles,1000)}

loadFiles();
</script>
</body></html>'''

@app.get("/api/files")
async def list_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT * FROM files ORDER BY upload_time DESC")
    files = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return {"files": files}

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if file.size > 100*1024*1024:
        raise HTTPException(400, "文件过大")
    
    filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    filepath = Path("files") / filename
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO files (filename, original_name, file_size) VALUES (?, ?, ?)",
                (filename, file.filename, len(content)))
    conn.commit()
    conn.close()
    
    return {"message": "上传成功", "url": f"/files/{filename}"}

@app.on_event("startup")
async def startup():
    init_db()
    print("🚀 SmartTravel 启动成功!")
    print("🌐 本地访问: http://localhost:8000")
    print("📁 文件管理: http://localhost:8000/file-manager")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 5. 创建启动服务
echo "⚙️ 创建系统服务..."
sudo tee /etc/systemd/system/smarttravel.service > /dev/null << EOF
[Unit]
Description=SmartTravel Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 6. 配置Nginx
echo "🌐 配置Nginx..."
sudo rm -f /etc/nginx/sites-enabled/default

sudo tee /etc/nginx/sites-available/smarttravel > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/smarttravel /etc/nginx/sites-enabled/
sudo nginx -t

# 7. 启动所有服务
echo "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable smarttravel
sudo systemctl start smarttravel
sudo systemctl restart nginx

# 8. 配置防火墙
echo "🔒 配置防火墙..."
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable

# 9. 配置SSL (如果域名解析正确)
echo "🔐 检查SSL配置..."
CURRENT_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ "$CURRENT_IP" = "$DOMAIN_IP" ]; then
    echo "✅ 域名解析正确，配置SSL..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive --redirect
    echo "✅ SSL配置完成"
else
    echo "⚠️ 域名解析待确认，请设置DNS记录:"
    echo "A记录: @ -> $CURRENT_IP"
    echo "A记录: www -> $CURRENT_IP"
fi

# 10. 完成部署
echo ""
echo "🎉 部署完成!"
echo "=================================="
echo "🔗 访问地址:"
echo "   HTTP:  http://$DOMAIN"
echo "   HTTPS: https://$DOMAIN (如SSL配置成功)"
echo "   文件:  http://$DOMAIN/file-manager"
echo "   API:   http://$DOMAIN/docs"
echo ""
echo "📊 服务状态:"
echo "   SmartTravel: $(sudo systemctl is-active smarttravel)"
echo "   Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "📋 管理命令:"
echo "   查看状态: sudo systemctl status smarttravel"
echo "   查看日志: sudo journalctl -u smarttravel -f"
echo "   重启服务: sudo systemctl restart smarttravel"
echo ""
echo "📂 项目目录: $PROJECT_DIR"