# MainProject/app/settings/root_settings.py
import gradio as gr


def system_info():
    # 这里你应该用实际代码动态获取
    return {
        "应用名称": "SmartTravel",
        "数据库主机": "8.153.88.50",
        "当前版本": "v1.2.3",
        "维护人员": "jiangxiaoxuan0316@gmail.com",
        "部署时间": "2024-05-31",
        "如有紧急问题，请联系": "13141736871"
    }


def update_site_info(name, desc, contact):
    # 这里应更新到数据库/配置，并可增加权限判断
    # 简单的模拟返回
    # 实际生产记得做权限校验和安全防护
    return f"已更新：站点名={name}，描述={desc}，联系方式={contact}"


def announcement_update(announcement):
    # 应实际存/发公告，略
    return f"公告已发布：{announcement}"


def fake_backup():
    # 调用实际备份命令
    return "【演示】系统备份已发起！（实际环境请实现备份逻辑）"


def root_settings():
    # 站点基础信息编辑区
    with gr.Blocks() as demo:
        gr.Markdown("## 🛡️ 最高权限-系统设置")

        with gr.Tab("基础信息"):
            sysinfobox = gr.JSON(label="当前系统信息", value=system_info())
            gr.Markdown(
                "**修改站点信息**"
            )
            sitename = gr.Textbox(label="站点名称", value="SmartTravel (演示版)")
            sitedesc = gr.Textbox(label="站点描述", value="AI智能出行与旅游平台")
            sitecontact = gr.Textbox(label="联系方式", value="admin@smarttravel.com")
            update_btn = gr.Button("保存设置")
            update_tip = gr.Textbox(label="操作反馈", interactive=False)
            update_btn.click(update_site_info, inputs=[sitename, sitedesc, sitecontact], outputs=update_tip)

        with gr.Tab("系统公告"):
            ann = gr.Textbox(label="公告内容", lines=4, placeholder="请填写公告内容")
            ann_btn = gr.Button("发布公告")
            ann_tip = gr.Textbox(label="反馈", interactive=False)
            ann_btn.click(announcement_update, inputs=ann, outputs=ann_tip)

        with gr.Tab("维护&备份"):
            gr.Markdown("**高危操作：建议定期备份，维护期间切勿随意关闭服务！**")
            backup_btn = gr.Button("系统立即备份")
            backup_tip = gr.Textbox(label="反馈", interactive=False)
            backup_btn.click(fn=fake_backup, outputs=backup_tip)

            gr.Markdown("> 这里可以添加：系统重启、缓存清理、数据恢复等高级按钮。")

        with gr.Tab("系统状态日志"):
            gr.Markdown("**服务运行日志预览功能请补充实现**")
            log_area = gr.Textbox(label="(打桩)系统日志快照", value="系统启动正常于 2024-05-31\n……", lines=8)

        gr.Markdown("**警告：此设置页仅超级管理员可见，请确保账户安全！**")
    return demo