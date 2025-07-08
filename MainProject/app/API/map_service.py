# MainProject/app/API/map_service.py
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

    def get_map_html(self, initial_place="", auto_locate_coords=None) -> str:
        # 自动定位脚本
        auto_locate_script = ""
        if auto_locate_coords:
            lng, lat = auto_locate_coords
            auto_locate_script = f"""
                // 页面加载完成后自动定位到指定坐标
                window.addEventListener('load', function() {{
                    setTimeout(function() {{
                        console.log('自动定位到坐标: {lng}, {lat}');

                        // 设置输入框值
                        document.getElementById('lng').value = {lng};
                        document.getElementById('lat').value = {lat};

                        // 更新地图中心和添加标记
                        if (map) {{
                            map.setCenter([{lng}, {lat}]);
                            map.setZoom({self.zoom});
                            addMarker({lng}, {lat});
                            reverseGeocode({lng}, {lat});
                        }}
                    }}, 1000);  // 增加延迟确保地图完全加载
                }});
                """

        # 自动搜索脚本
        auto_search_script = ""
        if initial_place:
            auto_search_script = f"""
                // 页面加载完成后自动搜索
                window.addEventListener('load', function() {{
                    setTimeout(function() {{
                        if (!document.getElementById('place').value) {{
                            document.getElementById('place').value = '{initial_place}';
                        }}
                    }}, 1500);
                }});
                """

        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TravelSmart - 位置查询工具</title>
            <style>
                html, body, #map-container {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                }}

                /* 整体容器 */
                .map-app {{
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }}

                /* 控制面板 */
                .control-panel {{
                    padding: 10px;
                    background: white;
                    border-bottom: 1px solid #e0e0e0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    z-index: 10;
                }}

                /* 地图容器 */
                #amap-container {{
                    flex: 1;
                    width: 100%;
                }}

                /* 输入框组 */
                .input-group {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;
                    width: 100%;
                    position: relative;
                }}

                .input-group label {{
                    width: 60px;
                    flex-shrink: 0;
                }}

                .input-group input[type="text"] {{
                    flex: 1;
                    padding: 5px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-family: monospace;
                    height: 28px;
                    box-sizing: border-box;
                }}

                .input-group button {{
                    padding: 5px 10px;
                    margin-left: 5px;
                    background: #0d6efd;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    height: 28px;
                }}

                .input-group button:hover {{
                    background: #0b5ed7;
                }}

                /* 坐标组 */
                .coord-group {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 8px;
                }}

                .coord-input {{
                    flex: 1;
                    display: flex;
                }}

                .coord-input label {{
                    width: 40px;
                    flex-shrink: 0;
                    line-height: 28px;
                }}

                .coord-input-wrapper {{
                    flex: 1;
                    display: flex;
                }}

                .coord-input-wrapper button {{
                    width: 28px;
                    height: 28px;
                    background: #f0f0f0;
                    border: 1px solid #ccc;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                }}

                .coord-input-wrapper button:hover {{
                    background: #e0e0e0;
                }}

                .coord-input-wrapper input {{
                    flex: 1;
                    border: 1px solid #ccc;
                    border-left: 0;
                    border-right: 0;
                    text-align: center;
                    font-family: monospace;
                    padding: 0 5px;
                    height: 28px;
                    box-sizing: border-box;
                }}

                /* 缩放滑块 */
                .zoom-slider-container {{
                    flex: 1;
                    min-width: 120px;
                }}

                .zoom-slider-header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}

                .zoom-slider-value {{
                    font-family: monospace;
                    font-weight: bold;
                }}

                .zoom-slider {{
                    width: 100%;
                    height: 28px;
                }}

                /* 工具按钮组 */
                .tools-group {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }}

                .tools-group button {{
                    padding: 5px 10px;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    cursor: pointer;
                    height: 28px;
                }}

                .tools-group button:hover {{
                    background: #e9ecef;
                }}

                /* 搜索建议框 */
                #sugg-box {{
                    position: absolute;
                    left: 60px;
                    top: 36px;
                    right: 65px;
                    z-index: 999;
                    background: #fff;
                    border-radius: 4px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    max-height: 280px;
                    overflow-y: auto;
                    display: none;
                }}

                #sugg-box div {{
                    cursor: pointer;
                    padding: 8px 12px;
                    border-bottom: 1px solid #f0f0f0;
                }}

                #sugg-box div:hover {{
                    background: #f0f7ff;
                    color: #0d6efd;
                }}

                /* 历史记录面板 */
                .history-panel {{
                    margin-top: 10px;
                    border-top: 1px solid #eee;
                    padding-top: 10px;
                }}

                .history-panel h6 {{
                    margin: 0 0 8px 0;
                    font-size: 14px;
                    font-weight: normal;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .history-toggle {{
                    background: none;
                    border: none;
                    color: #0d6efd;
                    cursor: pointer;
                    font-size: 12px;
                    padding: 2px 6px;
                    border-radius: 3px;
                    transition: background 0.2s;
                }}

                .history-toggle:hover {{
                    background: #e3f2fd;
                }}

                .history-list-container {{
                    max-height: 200px;
                    overflow-y: auto;
                    transition: max-height 0.3s ease;
                }}

                .history-list-container.collapsed {{
                    max-height: 120px; /* 大约3个项目的高度 */
                }}

                .history-item {{
                    cursor: pointer;
                    padding: 6px 8px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    margin-bottom: 5px;
                    font-size: 13px;
                    transition: all 0.2s;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .history-item:hover {{
                    background: #e9ecef;
                }}

                .history-item-content {{
                    flex: 1;
                    overflow: hidden;
                }}

                .history-item-name {{
                    font-weight: 500;
                    color: #333;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}

                .history-item-coords {{
                    color: #6c757d;
                    font-size: 11px;
                    margin-top: 2px;
                }}

                .history-item-delete {{
                    background: none;
                    border: none;
                    color: #dc3545;
                    cursor: pointer;
                    padding: 2px 4px;
                    border-radius: 2px;
                    font-size: 12px;
                    opacity: 0;
                    transition: opacity 0.2s;
                }}

                .history-item:hover .history-item-delete {{
                    opacity: 1;
                }}

                .history-item-delete:hover {{
                    background: #f8d7da;
                }}

                .history-empty {{
                    color: #6c757d;
                    text-align: center;
                    padding: 20px;
                    font-style: italic;
                }}

                /* 滚动条样式 */
                .history-list-container::-webkit-scrollbar {{
                    width: 4px;
                }}

                .history-list-container::-webkit-scrollbar-track {{
                    background: #f1f1f1;
                    border-radius: 2px;
                }}

                .history-list-container::-webkit-scrollbar-thumb {{
                    background: #c1c1c1;
                    border-radius: 2px;
                }}

                .history-list-container::-webkit-scrollbar-thumb:hover {{
                    background: #a8a8a8;
                }}

                /* 响应式调整 */
                @media (max-width: 768px) {{
                    .coord-group {{
                        flex-direction: column;
                    }}

                    .coord-input {{
                        width: 100%;
                    }}

                    .zoom-slider-container {{
                        width: 100%;
                    }}

                    .tools-group button {{
                        flex: 1;
                        font-size: 12px;
                    }}
                }}

                /* 信息窗体 */
                .marker-info {{
                    padding: 8px;
                    line-height: 1.5;
                    font-size: 13px;
                }}

                .copy-btn {{
                    color: #0d6efd;
                    cursor: pointer;
                    text-decoration: underline;
                    display: inline-block;
                    margin-top: 5px;
                }}

                /* 加载指示器 */
                .spinner-border {{
                    display: inline-block;
                    width: 1rem;
                    height: 1rem;
                    vertical-align: text-bottom;
                    border: 0.2em solid currentColor;
                    border-right-color: transparent;
                    border-radius: 50%;
                    animation: spinner-border .75s linear infinite;
                }}

                @keyframes spinner-border {{
                    to {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="map-app">
                <div class="control-panel">
                    <div class="input-group">
                        <label for="place">地点:</label>
                        <input type="text" id="place" placeholder="输入地点名称、地址或坐标">
                        <button id="search-btn">搜索</button>
                        <div id="sugg-box"></div>
                    </div>

                    <div class="coord-group">
                        <div class="coord-input">
                            <label>经度:</label>
                            <div class="coord-input-wrapper">
                                <button onclick="adjustCoord('lng', -0.01)">-</button>
                                <input type="text" id="lng" value="{self.center_lng}">
                                <button onclick="adjustCoord('lng', 0.01)">+</button>
                            </div>
                        </div>

                        <div class="coord-input">
                            <label>纬度:</label>
                            <div class="coord-input-wrapper">
                                <button onclick="adjustCoord('lat', -0.01)">-</button>
                                <input type="text" id="lat" value="{self.center_lat}">
                                <button onclick="adjustCoord('lat', 0.01)">+</button>
                            </div>
                        </div>

                        <div class="zoom-slider-container">
                            <div class="zoom-slider-header">
                                <span>缩放:</span>
                                <span class="zoom-slider-value" id="zoom-value">{self.zoom}.00</span>
                            </div>
                            <input type="range" min="3" max="19" step="0.1" value="{self.zoom}" class="zoom-slider" id="zoom-slider">
                        </div>
                    </div>

                    <div class="tools-group">
                        <button id="copy-coord-btn">复制坐标</button>
                        <button id="copy-url-btn">生成分享链接</button>
                        <button id="clear-marker-btn">清除标记</button>
                        <button id="reset-view-btn">重置视图</button>
                        <button id="map-type-btn">切换卫星图</button>
                        <button id="clear-history-btn">清空历史</button>
                    </div>
                </div>

                <div id="amap-container"></div>

                <div class="history-panel">
                    <h6>
                        <span>搜索历史</span>
                        <button id="history-toggle" class="history-toggle" style="display: none;">展开</button>
                    </h6>
                    <div id="history-list-container" class="history-list-container">
                        <div id="history-list"></div>
                    </div>
                </div>
            </div>

            <script src="https://webapi.amap.com/maps?v=2.0&key={self.amap_key}&plugin=AMap.Scale,AMap.Geocoder"></script>
            <script>
                // 初始化变量
                let map, marker, infoWindow, isSatelliteView = false;
                let isUpdatingFromMap = false;
                let isUpdatingFromInput = false;
                const geocoder = new AMap.Geocoder();

                // 获取历史记录的存储键名，基于当前URL创建唯一标识
                function getHistoryStorageKey() {{
                    try {{
                        const url = new URL(window.location.href);
                        const pathPart = url.pathname;
                        // 获取URL中可能的标识符参数
                        const mapId = url.searchParams.get('mapId') || '';
                        const userId = url.searchParams.get('userId') || '';
                        // 组合生成标识并进行编码
                        const identifier = pathPart + (mapId ? '_' + mapId : '') + (userId ? '_' + userId : '');
                        return 'map_history_' + btoa(identifier).replace(/[^a-zA-Z0-9]/g, '');
                    }} catch (e) {{
                        console.warn('生成历史记录键名失败，使用默认值:', e);
                        return 'map_history_default';
                    }}
                }}
    
                // 存储键名
                const HISTORY_STORAGE_KEY = getHistoryStorageKey();
    
                // 从URL参数或本地存储初始化位置
                const urlParams = new URLSearchParams(window.location.search);
                const initialLng = urlParams.get('lng') || localStorage.getItem('lastLng') || {self.center_lng};
                const initialLat = urlParams.get('lat') || localStorage.getItem('lastLat') || {self.center_lat};
                const initialZoom = urlParams.get('zoom') || localStorage.getItem('lastZoom') || {self.zoom};
    
                document.getElementById('lng').value = Number(initialLng).toFixed(5);
                document.getElementById('lat').value = Number(initialLat).toFixed(5);
                document.getElementById('zoom-slider').value = initialZoom;
                document.getElementById('zoom-value').textContent = Number(initialZoom).toFixed(2);
    
                // 初始化地图
                function initMap() {{
                    document.getElementById('amap-container').innerHTML = '<p style="padding:20px">地图加载中...</p>';
    
                    try {{
                        // 创建地图实例
                        map = new AMap.Map('amap-container', {{
                            center: [initialLng, initialLat],
                            zoom: initialZoom,
                            resizeEnable: true
                        }});
    
                        // 添加比例尺控件
                        map.addControl(new AMap.Scale());
    
                        // 地图事件
                        map.on('moveend', updateFromMap);
                        map.on('zoomend', updateFromMap);
                        map.on('mapmove', debounce(updateFromMap, 100));
                        map.on('zoom', debounce(updateFromMap, 100));
    
                        // 地图点击事件
                        map.on('click', function(e) {{
                            const lng = Math.round(e.lnglat.getLng() * 200) / 200;
                            const lat = Math.round(e.lnglat.getLat() * 200) / 200;
    
                            setInputValues(lng, lat);
                            addMarker(lng, lat);
    
                            // 反向地理编码获取地址
                            reverseGeocode(lng, lat);
                        }});
    
                        // 初始化输入框事件
                        initInputEvents();
    
                        // 初始化搜索建议
                        initSearchSuggestion();
    
                        // 初始加载历史记录
                        updateHistoryList();
    
                        // 父窗口消息监听
                        window.addEventListener('message', handleParentMessage);
    
                        // 处理URL中的坐标参数
                        if (urlParams.get('lng') && urlParams.get('lat')) {{
                            const lng = parseFloat(urlParams.get('lng'));
                            const lat = parseFloat(urlParams.get('lat'));
    
                            if (!isNaN(lng) && !isNaN(lat)) {{
                                addMarker(lng, lat);
                            }}
                        }}
    
                        // 如果URL有place参数，自动搜索
                        if (urlParams.get('place')) {{
                            document.getElementById('place').value = urlParams.get('place');
                            goSearch();
                        }}
                    }} catch (error) {{
                        console.error('地图初始化失败', error);
                        document.getElementById('amap-container').innerHTML = '<p style="color:red;padding:20px;">高德地图初始化失败: ' + error.message + '</p>';
                    }}
                }}
    
                // 处理父窗口消息
                function handleParentMessage(e) {{
                    if (e.data && e.data.type === 'set_location') {{
                        const lng = parseFloat(e.data.lng);
                        const lat = parseFloat(e.data.lat);
                        const zoom = parseFloat(e.data.zoom || map.getZoom());
    
                        if (!isNaN(lng) && !isNaN(lat)) {{
                            isUpdatingFromInput = true;
                            map.setCenter([lng, lat]);
                            setInputValues(lng, lat, zoom);
                            addMarker(lng, lat);
                            setTimeout(() => {{ isUpdatingFromInput = false; }}, 10);
                        }}
                    }}
                }}
    
                // 初始化输入框事件
                function initInputEvents() {{
                    // 经纬度输入框事件
                    document.getElementById('lng').addEventListener('input', debounce(updateFromInputs, 300));
                    document.getElementById('lat').addEventListener('input', debounce(updateFromInputs, 300));
    
                    // 缩放滑块事件
                    const zoomSlider = document.getElementById('zoom-slider');
                    zoomSlider.addEventListener('input', function() {{
                        document.getElementById('zoom-value').textContent = parseFloat(this.value).toFixed(2);
                    }});
                    zoomSlider.addEventListener('change', updateZoomFromSlider);
                    zoomSlider.addEventListener('input', debounce(updateZoomFromSlider, 50));
    
                    // 搜索按钮
                    document.getElementById('search-btn').addEventListener('click', goSearch);
                    document.getElementById('place').addEventListener('keydown', function(e) {{
                        if (e.key === "Enter") {{
                            if (document.getElementById('sugg-box').style.display === "block") {{
                                document.getElementById('sugg-box').style.display = "none";
                            }}
                            goSearch();
                        }}
                    }});
    
                    // 工具按钮
                    document.getElementById('copy-coord-btn').addEventListener('click', copyCoordinates);
                    document.getElementById('copy-url-btn').addEventListener('click', generateShareLink);
                    document.getElementById('clear-marker-btn').addEventListener('click', clearMarker);
                    document.getElementById('reset-view-btn').addEventListener('click', resetView);
                    document.getElementById('map-type-btn').addEventListener('click', toggleMapType);
                    document.getElementById('clear-history-btn').addEventListener('click', clearAllHistory);
                }}
    
                // 生成分享链接
                function generateShareLink() {{
                    const lng = document.getElementById('lng').value;
                    const lat = document.getElementById('lat').value;
                    const zoom = document.getElementById('zoom-slider').value;
                    const place = document.getElementById('place').value;
    
                    const url = `${{window.location.origin}}${{window.location.pathname}}?lng=${{lng}}&lat=${{lat}}&zoom=${{zoom}}${{place ? '&place=' + encodeURIComponent(place) : ''}}`;
    
                    try {{
                        navigator.clipboard.writeText(url).then(() => {{
                            alert('分享链接已复制到剪贴板：\\n' + url);
                        }}).catch(err => {{
                            fallbackCopy(url);
                        }});
                    }} catch (err) {{
                        fallbackCopy(url);
                    }}
                }}
    
                // 初始化搜索建议
                function initSearchSuggestion() {{
                    const placeInput = document.getElementById('place');
                    const suggBox = document.getElementById('sugg-box');
    
                    placeInput.addEventListener('input', debounce(function() {{
                        const kw = this.value.trim();
                        if (!kw) {{
                            suggBox.style.display = "none";
                            return;
                        }}
    
                        // 使用高德地图输入提示API
                        fetch(`https://restapi.amap.com/v3/assistant/inputtips?key={self.amap_key}&keywords=${{encodeURIComponent(kw)}}&datatype=all`)
                            .then(r => r.json())
                            .then(res => {{
                                if (!res.tips || !res.tips.length) {{
                                    suggBox.style.display = "none";
                                    return;
                                }}
    
                                suggBox.innerHTML = '';
                                let tipCount = 0;
    
                                res.tips.forEach(function(tip) {{
                                    if (!tip.name) return;
    
                                    const item = document.createElement('div');
                                    item.textContent = tip.name + (tip.district ? '（' + tip.district + '）' : '');
                                    if (tip.address) item.title = tip.address;
    
                                    item.onclick = function() {{
                                        placeInput.value = tip.name;
                                        suggBox.style.display = "none";
    
                                        if (tip.location) {{
                                            const arr = tip.location.split(',');
                                            const lng = Math.round(parseFloat(arr[0]) * 200) / 200;
                                            const lat = Math.round(parseFloat(arr[1]) * 200) / 200;
    
                                            setInputValues(lng, lat);
                                            map.setCenter([lng, lat]);
                                            addMarker(lng, lat);
    
                                            // 添加到历史记录
                                            addToHistory(tip.name, lng.toFixed(5), lat.toFixed(5));
                                        }} else {{
                                            goSearch();
                                        }}
                                    }};
    
                                    suggBox.appendChild(item);
                                    tipCount++;
                                }});
    
                                suggBox.style.display = tipCount > 0 ? "block" : "none";
                            }})
                            .catch(err => {{
                                console.warn('搜索建议请求失败:', err);
                                suggBox.style.display = "none";
                            }});
                    }}, 300));
    
                    // 点击空白处收起suggestions
                    document.addEventListener('mousedown', function(e) {{
                        if (!suggBox.contains(e.target) && e.target !== placeInput)
                            suggBox.style.display = "none";
                    }});
                }}
    
                // 从地图更新输入框
                function updateFromMap() {{
                    if (isUpdatingFromInput) return;
    
                    isUpdatingFromMap = true;
                    const center = map.getCenter();
                    const zoom = map.getZoom();
    
                    // 使用指定精度：经纬度精确到0.005，缩放精确到0.01
                    const lngRounded = Math.round(center.lng * 200) / 200;
                    const latRounded = Math.round(center.lat * 200) / 200;
                    const zoomRounded = Math.round(zoom * 100) / 100;
    
                    setInputValues(lngRounded, latRounded, zoomRounded);
    
                    // 保存到本地存储
                    localStorage.setItem('lastLng', lngRounded.toFixed(5));
                    localStorage.setItem('lastLat', latRounded.toFixed(5));
                    localStorage.setItem('lastZoom', zoomRounded.toFixed(2));
    
                    // 发送更新给父窗口
                    sendUpdateToParent(lngRounded, latRounded, zoomRounded);
    
                    setTimeout(() => {{ isUpdatingFromMap = false; }}, 10);
                }}
    
                // 从输入框更新地图
                function updateFromInputs() {{
                    if (isUpdatingFromMap) return;
    
                    isUpdatingFromInput = true;
                    const lng = parseFloat(document.getElementById('lng').value);
                    const lat = parseFloat(document.getElementById('lat').value);
    
                    if (!isNaN(lng) && !isNaN(lat)) {{
                        map.setCenter([lng, lat]);
    
                        if (marker) {{
                            marker.setPosition([lng, lat]);
                        }} else {{
                            addMarker(lng, lat);
                        }}
    
                        // 发送更新给父窗口
                        sendUpdateToParent(lng, lat, map.getZoom());
    
                        // 反向地理编码获取地址
                        reverseGeocode(lng, lat);
                    }}
    
                    setTimeout(() => {{ isUpdatingFromInput = false; }}, 10);
                }}
    
                // 更新缩放级别
                function updateZoomFromSlider() {{
                    if (isUpdatingFromMap) return;
    
                    isUpdatingFromInput = true;
                    const zoom = parseFloat(document.getElementById('zoom-slider').value);
    
                    if (!isNaN(zoom)) {{
                        map.setZoom(zoom);
                        // 发送更新给父窗口
                        const center = map.getCenter();
                        sendUpdateToParent(center.lng, center.lat, zoom);
                    }}
    
                    setTimeout(() => {{ isUpdatingFromInput = false; }}, 10);
                }}
    
                // 设置输入框的值
                function setInputValues(lng, lat, zoom) {{
                    document.getElementById('lng').value = lng.toFixed(5);
                    document.getElementById('lat').value = lat.toFixed(5);
    
                    if (zoom !== undefined) {{
                        document.getElementById('zoom-slider').value = zoom;
                        document.getElementById('zoom-value').textContent = zoom.toFixed(2);
                    }}
                }}
    
                // 添加标记
                function addMarker(lng, lat) {{
                    // 清除已有标记
                    if (marker) {{
                        map.remove(marker);
                    }}
    
                    // 创建新标记
                    marker = new AMap.Marker({{
                        position: [lng, lat],
                        animation: 'AMAP_ANIMATION_DROP',
                        map: map
                    }});
    
                    // 创建信息窗体
                    if (!infoWindow) {{
                        infoWindow = new AMap.InfoWindow({{
                            offset: new AMap.Pixel(0, -30)
                        }});
                    }}
    
                    // 更新信息窗体内容
                    updateInfoWindow(lng, lat);
    
                    // 标记点击事件
                    marker.on('click', function() {{
                        updateInfoWindow(lng, lat);
                        infoWindow.open(map, marker.getPosition());
                    }});
                }}
    
                // 更新信息窗体
                function updateInfoWindow(lng, lat, address = '') {{
                    if (!infoWindow || !marker) return;
    
                    let content = `
                        <div class="marker-info">
                            <div>经度：${{lng.toFixed(5)}}</div>
                            <div>纬度：${{lat.toFixed(5)}}</div>
                    `;
    
                    if (address) {{
                        content += `<div>地址：${{address}}</div>`;
                    }}
    
                    content += `
                            <div style="margin-top:5px">
                                <span class="copy-btn" onclick="copyCoordinates()">复制坐标</span>
                            </div>
                        </div>
                    `;
    
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker.getPosition());
                }}
    
                // 反向地理编码
                function reverseGeocode(lng, lat) {{
                    geocoder.getAddress([lng, lat], function(status, result) {{
                        if (status === 'complete' && result.info === 'OK') {{
                            const address = result.regeocode.formattedAddress;
                            document.getElementById('place').value = address;
                            updateInfoWindow(lng, lat, address);
                        }}
                    }});
                }}

                // 地点搜索
                function goSearch() {{
                    const place = document.getElementById('place').value.trim();
                    if (!place) return;
    
                    // 显示加载状态
                    const searchBtn = document.getElementById('search-btn');
                    const originalText = searchBtn.textContent;
                    searchBtn.innerHTML = '<span class="spinner-border" role="status" aria-hidden="true"></span> 搜索中';
                    searchBtn.disabled = true;
    
                    // 先尝试解析坐标格式 (经度,纬度)
                    const coordMatch = place.match(/^\\s*(\\d+\\.?\\d*)\\s*[,，]\\s*(\\d+\\.?\\d*)\\s*$/);
                    if (coordMatch) {{
                        const lng = parseFloat(coordMatch[1]);
                        const lat = parseFloat(coordMatch[2]);
    
                        if (!isNaN(lng) && !isNaN(lat)) {{
                            setInputValues(lng, lat);
                            map.setCenter([lng, lat]);
                            addMarker(lng, lat);
                            addToHistory("坐标", lng.toFixed(5), lat.toFixed(5));
                            searchBtn.innerHTML = originalText;
                            searchBtn.disabled = false;
                            return;
                        }}
                    }}
    
                    // Step 1: 先尝试inputtips
                    fetch(`https://restapi.amap.com/v3/assistant/inputtips?key={self.amap_key}&keywords=${{encodeURIComponent(place)}}&datatype=all`)
                        .then(r => r.json())
                        .then(res => {{
                            for (let tip of res.tips || []) {{
                                if (tip.location) {{
                                    const arr = tip.location.split(',');
                                    const lng = Math.round(parseFloat(arr[0]) * 200) / 200;
                                    const lat = Math.round(parseFloat(arr[1]) * 200) / 200;
    
                                    setInputValues(lng, lat);
                                    map.setCenter([lng, lat]);
                                    addMarker(lng, lat);
                                    addToHistory(tip.name || place, lng.toFixed(5), lat.toFixed(5));
    
                                    searchBtn.innerHTML = originalText;
                                    searchBtn.disabled = false;
                                    return;
                                }}
                            }}
    
                            // Step 2: 如果没有结果，再尝试geocode
                            geocoder.getLocation(place, function(status, result) {{
                                searchBtn.innerHTML = originalText;
                                searchBtn.disabled = false;
    
                                if (status === 'complete' && result.info === 'OK') {{
                                    if (result.geocodes.length > 0) {{
                                        const location = result.geocodes[0].location;
                                        const lng = Math.round(location.lng * 200) / 200;
                                        const lat = Math.round(location.lat * 200) / 200;
    
                                        setInputValues(lng, lat);
                                        map.setCenter([lng, lat]);
                                        addMarker(lng, lat);
                                        addToHistory(result.geocodes[0].formatted_address || place, lng.toFixed(5), lat.toFixed(5));
                                    }} else {{
                                        alert('未找到该地点');
                                    }}
                                }} else {{
                                    alert('搜索失败: ' + result.info);
                                }}
                            }});
                        }})
                        .catch(e => {{
                            searchBtn.innerHTML = originalText;
                            searchBtn.disabled = false;
                            alert('请求出错！');
                            console.error(e);
                        }});
                }}
    
                // 历史记录功能
                function addToHistory(name, lng, lat) {{
                    try {{
                        let history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
    
                        // 检查是否已存在相同记录，避免重复
                        const exists = history.some(item => item.lng === lng && item.lat === lat);
                        if (exists) return;
    
                        // 添加新记录
                        history.unshift({{
                            name: name,
                            lng: lng,
                            lat: lat,
                            time: new Date().toLocaleString()
                        }});
    
                        // 限制历史记录数量
                        if (history.length > 20) {{
                            history = history.slice(0, 20);
                        }}
    
                        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
                        updateHistoryList();
                    }} catch (e) {{
                        console.warn('添加历史记录失败:', e);
                    }}
                }}
    
                // 更新历史记录列表 - 修复后的唯一版本
                function updateHistoryList() {{
                    try {{
                        const historyList = document.getElementById('history-list');
                        const historyContainer = document.getElementById('history-list-container');
                        const historyToggle = document.getElementById('history-toggle');
                        
                        if (!historyList || !historyContainer || !historyToggle) {{
                            console.warn('历史记录元素未找到');
                            return;
                        }}
    
                        const history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
    
                        historyList.innerHTML = '';
    
                        if (history.length === 0) {{
                            historyList.innerHTML = '<div class="history-empty">暂无历史记录</div>';
                            historyToggle.style.display = 'none';
                            historyContainer.classList.remove('collapsed');
                            return;
                        }}
    
                        // 根据历史记录数量决定是否显示折叠按钮
                        if (history.length > 3) {{
                            historyToggle.style.display = 'block';
                            historyContainer.classList.add('collapsed');
                            historyToggle.textContent = '展开 (' + history.length + ')';
                        }} else {{
                            historyToggle.style.display = 'none';
                            historyContainer.classList.remove('collapsed');
                        }}
    
                        history.forEach((item, index) => {{
                            const historyItem = document.createElement('div');
                            historyItem.className = 'history-item';
                            historyItem.innerHTML = `
                                <div class="history-item-content">
                                    <div class="history-item-name" title="${{item.name}} - ${{item.time}}">${{item.name}}</div>
                                    <div class="history-item-coords">${{item.lng}}, ${{item.lat}}</div>
                                </div>
                                <button class="history-item-delete" onclick="deleteHistoryItem(${{index}})" title="删除">×</button>
                            `;
    
                            // 点击历史项目恢复位置
                            historyItem.addEventListener('click', function(e) {{
                                // 如果点击的是删除按钮，不执行恢复位置
                                if (e.target.classList.contains('history-item-delete')) {{
                                    return;
                                }}
    
                                isUpdatingFromInput = true;
                                document.getElementById('lng').value = item.lng;
                                document.getElementById('lat').value = item.lat;
                                document.getElementById('place').value = item.name;
                                setTimeout(() => {{ isUpdatingFromInput = false; }}, 10);
    
                                map.setCenter([parseFloat(item.lng), parseFloat(item.lat)]);
                                addMarker(parseFloat(item.lng), parseFloat(item.lat));
                            }});
    
                            historyList.appendChild(historyItem);
                        }});
    
                        // 绑定折叠/展开事件
                        historyToggle.onclick = function() {{
                            const isCollapsed = historyContainer.classList.contains('collapsed');
                            if (isCollapsed) {{
                                historyContainer.classList.remove('collapsed');
                                historyToggle.textContent = '折叠';
                            }} else {{
                                historyContainer.classList.add('collapsed');
                                historyToggle.textContent = '展开 (' + history.length + ')';
                            }}
                        }};
                    }} catch (e) {{
                        console.error('更新历史记录列表失败:', e);
                    }}
                }}
    
                // 删除历史记录项目的函数
                function deleteHistoryItem(index) {{
                    try {{
                        let history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
                        
                        if (index >= 0 && index < history.length) {{
                            history.splice(index, 1);
                            localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
                            updateHistoryList();
                        }}
                    }} catch (e) {{
                        console.warn('删除历史记录失败:', e);
                    }}
                }}
    
                // 清空所有历史记录的函数
                function clearAllHistory() {{
                    if (confirm('确定要清空所有历史记录吗？')) {{
                        try {{
                            localStorage.removeItem(HISTORY_STORAGE_KEY);
                            updateHistoryList();
                        }} catch (e) {{
                            console.warn('清空历史记录失败:', e);
                        }}
                    }}
                }}
    
                // 调整经纬度
                function adjustCoord(type, delta) {{
                    const input = document.getElementById(type);
                    let value = parseFloat(input.value);
    
                    if (!isNaN(value)) {{
                        // 加上增量并精确到0.005
                        value = Math.round((value + delta) * 200) / 200;
                        input.value = value.toFixed(5);
    
                        // 触发输入事件以更新地图
                        const event = new Event('input', {{ bubbles: true }});
                        input.dispatchEvent(event);
                    }}
                }}
    
                // 复制坐标
                function copyCoordinates() {{
                    const lng = document.getElementById('lng').value;
                    const lat = document.getElementById('lat').value;
                    const text = `${{lng}},${{lat}}`;
    
                    try {{
                        navigator.clipboard.writeText(text).then(() => {{
                            alert('坐标已复制到剪贴板: ' + text);
                        }}).catch(err => {{
                            fallbackCopy(text);
                        }});
                    }} catch (err) {{
                        fallbackCopy(text);
                    }}
                }}
    
                // 复制坐标的备用方法
                function fallbackCopy(text) {{
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
    
                    try {{
                        document.execCommand('copy');
                        alert('坐标已复制到剪贴板: ' + text);
                    }} catch (err) {{
                        alert('复制失败，请手动复制: ' + text);
                    }}
    
                    document.body.removeChild(textarea);
                }}
    
                // 清除标记
                function clearMarker() {{
                    if (marker) {{
                        map.remove(marker);
                        marker = null;
                    }}
    
                    if (infoWindow) {{
                        infoWindow.close();
                    }}
                }}
    
                // 重置视图
                function resetView() {{
                    map.setCenter([{self.center_lng}, {self.center_lat}]);
                    map.setZoom({self.zoom});
    
                    setInputValues({self.center_lng}, {self.center_lat}, {self.zoom});
    
                    if (marker) {{
                        map.remove(marker);
                        marker = null;
                    }}
    
                    if (infoWindow) {{
                        infoWindow.close();
                    }}
    
                    document.getElementById('place').value = '';
    
                    // 发送更新给父窗口
                    sendUpdateToParent({self.center_lng}, {self.center_lat}, {self.zoom});
                }}
    
                // 切换地图类型
                function toggleMapType() {{
                    isSatelliteView = !isSatelliteView;
    
                    if (isSatelliteView) {{
                        map.setLayers([new AMap.TileLayer.Satellite()]);
                        document.getElementById('map-type-btn').textContent = '切换普通图';
                    }} else {{
                        map.setLayers([new AMap.TileLayer()]);
                        document.getElementById('map-type-btn').textContent = '切换卫星图';
                    }}
                }}
    
                // 发送更新给父窗口
                function sendUpdateToParent(lng, lat, zoom) {{
                    try {{
                        window.parent.postMessage({{
                            amap_update: true,
                            center: [Number(lng), Number(lat)],
                            zoom: Number(zoom)
                        }}, '*');
                    }} catch (e) {{
                        console.warn('发送消息给父窗口失败:', e);
                    }}
                }}
    
                // 防抖函数
                function debounce(func, wait) {{
                    let timeout;
                    return function(...args) {{
                        const context = this;
                        clearTimeout(timeout);
                        timeout = setTimeout(() => func.apply(context, args), wait);
                    }};
                }}
    
                // 初始化地图
                if (typeof AMap !== 'undefined') {{
                    initMap();
                }} else {{
                    window.onload = function() {{
                        if (typeof AMap !== 'undefined') {{
                            initMap();
                        }} else {{
                            document.getElementById('amap-container').innerHTML = '<p style="color:red;padding:20px;">高德地图JS加载失败，请检查密钥</p>';
                        }}
                    }};
                }}
                {auto_locate_script}
                {auto_search_script}
            </script>
        </body>
        </html>
        """



