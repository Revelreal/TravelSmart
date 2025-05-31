import os
import toml


class MapService:
    center_lng: float = 116.397428
    center_lat: float = 39.90923
    zoom: int = 13

    def __init__(self):
        self.center = [116.397428, 39.90923]
        self.zoom = 13
        cfg_path = os.path.join(os.path.dirname(__file__), "../../../config.toml")
        cfg = toml.load(cfg_path)
        self.amap_key = cfg["amap"]["amap_key"]

    def get_map_html(self) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                html, body, #map {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script src="https://webapi.amap.com/maps?v=2.0&key={self.amap_key}"></script>
            <script>
                document.getElementById('map').innerHTML = '<p style="padding:20px">地图加载中...</p>';

                window.onload = function() {{
                    if(typeof AMap === 'undefined') {{
                        document.getElementById('map').innerHTML = '<p style="color:red">高德地图JS加载失败，请检查密钥</p>';
                        return;
                    }}

                    var map = new AMap.Map('map', {{
                        center: {self.center},
                        zoom: {self.zoom},
                        resizeEnable: true
                    }});

                    // 父窗口发送消息时：移动/缩放地图（输入框变动→地图刷新）
                    window.addEventListener('message', function(e) {{
                        if (e.data && e.data.center) map.setCenter(e.data.center);
                        if (e.data && e.data.zoom) map.setZoom(e.data.zoom);
                    }});

                    // 地图被拖动或缩放后：把中心和缩放等级发给父窗口（地图操作→输入框刷新）
                    function sendToParent() {{
                        var center = map.getCenter();
                        var zoom = map.getZoom();
                        window.parent.postMessage({{
                            amap_update: true,
                            center: [Number(center.lng), Number(center.lat)],
                            zoom: zoom
                        }}, '*');
                    }}
                    map.on('moveend', sendToParent);
                    map.on('zoomend', sendToParent);
                }};
            </script>
        </body>
        </html>
        """
