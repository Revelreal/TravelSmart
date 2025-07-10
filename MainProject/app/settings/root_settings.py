import gradio as gr
from gradio import Request  # 必须用 gradio.Request，不是 fastapi.Request
from MainProject.auth_utils import verify_token


def require_token(token):
    info = verify_token(token)
    if not info or not info.get("username"):
        raise gr.Error("认证失败或无权限，请重新登录")
    if info.get("role") not in ("root", "superuser"):
        raise gr.Error("仅允许ROOT用户访问本设置页！")
    return info


def system_info():
    return {
        "应用名称": "SmartTravel",
        "数据库主机": "8.153.88.50",
        "当前版本": "v1.2.3",
        "维护人员": "jiangxiaoxuan0316@gmail.com",
        "部署时间": "2024-05-31",
        "如有紧急问题，请联系": "13141736871"
    }


def update_site_info(name, desc, contact, token):
    require_token(token)
    return f"已更新：站点名={name}，描述={desc}，联系方式={contact}"


def announcement_update(announcement, token):
    require_token(token)
    return f"公告已发布：{announcement}"


def fake_backup(token):
    require_token(token)
    return "【演示】系统备份已发起！（实际环境请实现备份逻辑）"


def create_root_settings():
    with gr.Blocks() as demo:
        token_box = gr.Textbox(visible=False, elem_id="root_settings_token_box")
        adminbar = gr.Markdown("正在认证超级管理员身份...")

        def load_admin_settings(request: Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("认证失败，请重新登录")
            if info.get("role") not in ("root", "superuser"):
                raise gr.Error("仅允许ROOT用户访问本设置页！")
            username = info["username"]
            welcome_msg = f"🛡️ {username}（ROOT），欢迎使用系统设置中心"
            return token, welcome_msg

        # 这里关键，只依赖Gradio的load事件
        demo.load(
            load_admin_settings,  # 回调函数，唯一参数是gradio.Request
            None,  # 无inputs，由request对象传token
            [token_box, adminbar]  # outputs正常流转
        )

        sysinfobox = gr.JSON(label="当前系统信息", value=system_info())

        with gr.Tab("基础信息"):
            gr.Markdown("**修改站点信息**")
            sitename = gr.Textbox(label="站点名称", value="SmartTravel (演示版)")
            sitedesc = gr.Textbox(label="站点描述", value="AI智能出行与旅游平台")
            sitecontact = gr.Textbox(label="联系方式", value="admin@smarttravel.com")
            update_btn = gr.Button("保存设置")
            update_tip = gr.Textbox(label="操作反馈", interactive=False)
            update_btn.click(
                update_site_info,
                inputs=[sitename, sitedesc, sitecontact, token_box],
                outputs=update_tip
            )

        with gr.Tab("系统公告"):
            ann = gr.Textbox(label="公告内容", lines=4, placeholder="请填写公告内容")
            ann_btn = gr.Button("发布公告")
            ann_tip = gr.Textbox(label="反馈", interactive=False)
            ann_btn.click(announcement_update, inputs=[ann, token_box], outputs=ann_tip)

        with gr.Tab("维护&备份"):
            gr.Markdown("**高危操作：建议定期备份，维护期间切勿随意关闭服务！**")
            backup_btn = gr.Button("系统立即备份")
            backup_tip = gr.Textbox(label="反馈", interactive=False)
            backup_btn.click(fake_backup, inputs=[token_box], outputs=backup_tip)
            gr.Markdown("> 这里可以添加：系统重启、缓存清理、数据恢复等高级按钮。")

        with gr.Tab("系统状态日志"):
            gr.Markdown("**服务运行日志预览功能请补充实现**")
            log_area = gr.Textbox(label="(打桩)系统日志快照", value="系统启动正常于 2024-05-31\n……", lines=8)

        gr.Markdown("**警告：此设置页仅超级管理员可见，请确保账户安全！**")
    return demo
