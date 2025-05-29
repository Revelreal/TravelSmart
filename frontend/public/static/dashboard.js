// 折叠按钮
const sidebar = document.querySelector('.sidebar');
const rightbar = document.querySelector('.rightbar');
const dragbarLeft = document.querySelector('.dragbar-left');
const dragbarRight = document.querySelector('.dragbar-right');
document.querySelector('.left-toggle').onclick = function() {
    const isCollapsed = sidebar.classList.toggle('collapsed');
    dragbarLeft.classList.toggle('disabled', isCollapsed);
};
document.querySelector('.right-toggle').onclick = function() {
    const isCollapsed = rightbar.classList.toggle('collapsed');
    dragbarRight.classList.toggle('disabled', isCollapsed);
};
// 拖拽逻辑，宽度只影响浮层自身
function dragResize(resizer, target, isLeft, minW, maxW) {
    let dragging = false, startX = 0, startW = 0;
    resizer.addEventListener('mousedown', function(e) {
        if(resizer.classList.contains('disabled') || target.classList.contains('collapsed')) return;
        dragging = true;
        document.body.style.userSelect = "none";
        resizer.classList.add('dragging');
        startX = e.clientX;
        startW = target.getBoundingClientRect().width;
        e.preventDefault();
    });
    window.addEventListener('mousemove', function(e){
        if(!dragging) return;
        let dx = e.clientX - startX;
        let newW = isLeft ? (startW + dx) : (startW - dx);
        if(newW < minW) newW = minW; if(newW > maxW) newW = maxW;
        target.style.width = newW + "px";
    });
    window.addEventListener('mouseup', function(e){
        if(!dragging) return;
        dragging = false;
        document.body.style.userSelect = "";
        resizer.classList.remove('dragging');
    });
}
dragResize(dragbarLeft, sidebar, true, 140, 400);
dragResize(dragbarRight, rightbar, false, 140, 400);
// 初始禁用
dragbarLeft.classList.toggle('disabled', sidebar.classList.contains('collapsed'));
dragbarRight.classList.toggle('disabled', rightbar.classList.contains('collapsed'));

// 地图懒加载，加载后全屏中间显示
let amapLoaded = false;
document.getElementById('load-map-btn').onclick = function() {
    if (amapLoaded) return;
    const ph = document.getElementById('map-placeholder');
    ph.innerHTML = '<div id="map-container"></div>';
    if (!window.AMap) {
        const script = document.createElement("script");
        script.src = "https://webapi.amap.com/maps?v=2.0&key=513fce8c9a3e2473fad5b2a2963d8c4f";
        script.onload = renderMap;
        document.body.appendChild(script);
    } else { renderMap(); }
    amapLoaded = true;
    this.disabled = true;
    this.textContent = "地图已加载";
    this.style.opacity = "0.66";
};
function renderMap() {
    new AMap.Map('map-container', {
        zoom: 11, center: [116.3212, 39.9346],
        viewMode:'2D'
    });
}

// AI 聊天
document.getElementById('chat-form').onsubmit = async function(e){
    e.preventDefault();
    let inputBox = document.getElementById('chat-input');
    let msg = inputBox.value.trim();
    if(!msg) return;
    let hist = document.getElementById('chat-history');
    let userDiv = document.createElement('div');
    userDiv.textContent = "你：" + msg;
    hist.appendChild(userDiv);
    inputBox.value = '';
    let aiDiv = document.createElement('div');
    aiDiv.textContent = "AI助手：思考中...";
    aiDiv.style.color = "#3779e3";
    hist.appendChild(aiDiv);
    hist.scrollTop = hist.scrollHeight;
    try {
        let resp = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: msg})
        });
        let data = await resp.json();
        let md = data.answer || "无回复";
        aiDiv.style.color = "#222";
        aiDiv.innerHTML = "<b>AI助手：</b>" + marked.parse(md);
        hist.scrollTop = hist.scrollHeight;
    } catch (e) {
        aiDiv.textContent = "AI助手：请求失败";
        aiDiv.style.color = "#f33";
    }
};