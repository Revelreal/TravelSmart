// 高德地图初始化
window.onload = function() {
    let map = new AMap.Map('map-container', {
        zoom: 11,
        center: [116.397428, 39.90923] // 默认北京，可替换为用户偏好
    });

    // 假如已登录用户信息存在（后端渲染或者JS写入），你可以动态填充名称
    // document.getElementById('user-name').textContent = 获取的用户名;
};

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

    // 显示AI助手正在回复（可选优化体验）
    let aiDiv = document.createElement('div');
    aiDiv.textContent = "AI助手：思考中...";
    aiDiv.style.color = "#3779e3";
    hist.appendChild(aiDiv);
    hist.scrollTop = hist.scrollHeight;

    try {
        // 异步请求后端AI接口
        let resp = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: msg})
        });
        let data = await resp.json();
        aiDiv.textContent = "AI助手：" + data.answer;
        hist.scrollTop = hist.scrollHeight;
    } catch (e) {
        aiDiv.textContent = "AI助手：请求失败，请稍后再试";
        aiDiv.style.color = "#f33";
    }
};