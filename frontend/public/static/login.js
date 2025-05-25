document.addEventListener("DOMContentLoaded", function() {
    let form = document.getElementById("loginForm");
    let errmsg = document.getElementById("errmsg");

    form.onsubmit = function(e) {
        e.preventDefault();
        errmsg.textContent = "";
        let uname = document.getElementById("username").value.trim();
        let pwd = document.getElementById("password").value;

        fetch("/login", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({username: uname, password: pwd})
        })
        .then(resp => resp.json().then(data => ({status: resp.status, ...data})))
        .then(res => {
            if(res.status === 200){
                errmsg.style.color = "green";
                errmsg.textContent = "登录成功，正在跳转...";
                setTimeout(function(){
                    window.location.href = "/dashboard";
                }, 800);
            }else{
                errmsg.style.color = "red";
                errmsg.textContent = res.detail || "用户名或密码错误";
            }
        })
        .catch(function(){
            errmsg.style.color = "red";
            errmsg.textContent = "网络异常，请稍后再试";
        });
    };
});