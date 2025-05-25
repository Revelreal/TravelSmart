// 高德地图初始化
window.onload = function() {
    let map = new AMap.Map('map-container', {
        zoom: 11,
        center: [116.397428, 39.90923] // 默认北京，可替换为用户偏好
    });

    // 假如已登录用户信息存在（后端渲染或者JS写入），你可以动态填充名称
    // document.getElementById('user-name').textContent = 获取的用户名;
};

// 简单AI问答区（仅前端示例，需结合API实现真正交互）
document.getElementById('chat-form').onsubmit = function(e){
    e.preventDefault();
    let inputBox = document.getElementById('chat-input');
    let msg = inputBox.value.trim();
    if(!msg) return;
    let hist = document.getElementById('chat-history');
    let userDiv = document.createElement('div');
    userDiv.textContent = "你：" + msg;
    hist.appendChild(userDiv);

    // 演示：假装AI回复
    setTimeout(() => {
        let aiDiv = document.createElement('div');
        aiDiv.textContent = "AI助手：" + "（这里是AI回复内容, 实际应调用后端API）";
        aiDiv.style.color = "#3779e3";
        hist.appendChild(aiDiv);
        hist.scrollTop = hist.scrollHeight;
    }, 600);

    inputBox.value = '';
};