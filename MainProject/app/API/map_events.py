# app/API/map_events.py

import os


def amap_html():
    # 获取静态资源目录“static/amap_embed.html”绝对路径
    html_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "app", "static", "amap_embed.html"
    )
    html_file = os.path.abspath(html_file)
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()
