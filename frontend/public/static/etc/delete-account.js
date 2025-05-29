// 你可以加前端二次确认、弹窗等，这里只做简单提交处理。
// 假定后端 /logout POST 返回 {success: true}，自动跳转首页
document.getElementById('logout-form').onsubmit = async function(e) {
    e.preventDefault();
    const btn = document.querySelector('.logout-btn');
    btn.disabled = true;
    btn.textContent = '正在注销...';
    try {
        let resp = await fetch('/etc/delete-account', { method: 'POST' });
        let data = await resp.json();
        if (data.success) {
            btn.textContent = '注销成功，正在跳转...';
            setTimeout(() => { window.location.href = '/'; }, 1200);
        } else {
            btn.disabled = false;
            btn.textContent = '注销账号';
            alert(data.message || '注销失败');
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = '注销账号';
        alert('网络异常，注销失败');
    }
};