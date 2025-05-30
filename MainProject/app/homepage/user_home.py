# app/homepage/user_home.py

import gradio as gr
from MainProject.app.API.map_events import amap_html


def user_home_page():
    with gr.Blocks(title="用户主页") as demo:
        # 自定义样式&按钮布局
        gr.HTML("""
                <style>
                #sidebar {position:fixed; left:-240px; top:0; bottom:0; width:220px; background:#263445; box-shadow:2px 0 10px rgba(0,0,0,.1); transition:.3s; z-index:999;}
                #sidebar.active {left:0;}
                #open_sidebar_btn {position:fixed; left:30px; bottom:30px; z-index:1001;}
                #chatbot_area {position:fixed; right:-340px; bottom:0; width:320px; height:70vh; background:#fff; border-left:1px solid #eee; box-shadow: -4px 0 18px rgba(0,0,0,.08); transition:.3s; z-index:999;}
                #chatbot_area.active {right: 0;}
                #open_chatbot_btn {position:fixed; right:30px; bottom:30px; z-index:1001;}
                </style>
                """)
        # 左侧菜单
        gr.HTML("""
                <div id="sidebar">
                    <div style="color:#fff; padding:24px 16px 10px;font-size:17px;font-weight:bold;">导航菜单</div>
                    <ul style="list-style:none;padding:0 18px;">
                        <li><a href="/homepage/user_home" style="color:#fff;display:block;padding:7px 0;">🏠 我的主页</a></li>
                        <li><a href="/homepage/settings/profile" style="color:#fff;display:block;padding:7px 0;">⚙️ 设置</a></li>
                        <li><a href="/homepage/settings/help" style="color:#fff;display:block;padding:7px 0;">❓ 帮助</a></li>
                        <li><a href="/homepage/settings/logout" style="color:#fff;display:block;padding:7px 0;">🚪 登出</a></li>
                    </ul>
                    <div style="position:absolute;bottom:16px;left:0;right:0;text-align:center;"><small style="color:#888;">TravelSmart &copy; 2024</small></div>
                </div>
                """)

        # 右侧AI聊天窗口（iframe示例，可挂AI聊天网页/Gradio聊天）
        gr.HTML("""
                <div id="chatbot_area">
                    <div style="background:#16a085; color:#fff; padding:14px 10px;font-weight:bold;">🤖 AI助手
                        <button onclick="document.getElementById('chatbot_area').classList.remove('active')" style="float:right;background:none;border:none;color:white;font-size:18px;">×</button>
                    </div>
                    <iframe src="/ai_chat" style="width:100%;height:calc(100% - 48px);border:none;"></iframe>
                </div>
                """)

        # 地图主体
        gr.HTML(f'{amap_html()}')

        # 左下悬浮按钮：呼出菜单
        gr.HTML("""
                <button id="open_sidebar_btn"
                 style="position:fixed; left:30px; bottom:30px; background:#263445;color:#fff;border:none;border-radius:50%;width:52px;height:52px;font-size:25px;box-shadow:0 2px 8px rgba(70,70,70,.13);cursor:pointer;z-index:1001;">≡</button>
                        """)

        # 右下悬浮按钮：呼出AI聊天
        gr.HTML("""
                <button id="open_chatbot_btn"
                 style="position:fixed; right:30px; bottom:30px; background:#16a085;color:#fff;border:none;border-radius:50%;width:52px;height:52px;font-size:26px;box-shadow:0 2px 8px rgba(70,70,70,.13);cursor:pointer;z-index:1001;">🤖</button>
                        """)

        # 绑定JS交互
        gr.HTML("""
                <script>
                document.getElementById('open_sidebar_btn').onclick = function(){
                    var sbar = document.getElementById('sidebar');
                    if (sbar.classList.contains('active')) sbar.classList.remove('active');
                    else sbar.classList.add('active');
                };
                document.getElementById('open_chatbot_btn').onclick = function(){
                    var cbar = document.getElementById('chatbot_area');
                    if (cbar.classList.contains('active')) cbar.classList.remove('active');
                    else cbar.classList.add('active');
                };
                document.addEventListener('keydown',function(e){
                    if(e.key==="Escape"){
                        document.getElementById('sidebar').classList.remove('active');
                        document.getElementById('chatbot_area').classList.remove('active');
                    }
                });
                </script>
                """)
    return demo
