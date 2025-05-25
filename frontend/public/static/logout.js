document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("logoutConfirmBtn").onclick = function() {
        fetch("/etc/logout", {
            method: "POST",
            credentials: "include" // 如果你的登录状态基于cookie
        })
        .then(resp => resp.json().then(data => ({status:resp.status, ...data})))
        .then(res => {
            let msg = document.getElementById("logoutMsg");
            if(res.status === 200) {
                msg.textContent = "注销成功，正在跳转首页...";
                setTimeout(() => {
                    location.href = "/index";
                }, 900);
            } else {
                msg.textContent = res.detail || "注销失败";
            }
        })
        .catch(() => {
            document.getElementById("logoutMsg").textContent = "网络异常，请稍后再试。";
        });
    };
});