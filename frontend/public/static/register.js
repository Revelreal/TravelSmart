document.getElementById('registerForm').onsubmit = function(e) {
    e.preventDefault();
    let valid = true;
    // 清除提示
    ['userTip','emailTip','pwdTip','cpwdTip'].forEach(id=>{document.getElementById(id).textContent='';});

    let uname = document.getElementById('username').value.trim();
    let email = document.getElementById('email').value.trim();
    let pwd = document.getElementById('password').value;
    let cpwd = document.getElementById('confirm').value;

    if(!uname){
        document.getElementById('userTip').textContent='请输入用户名';
        valid=false;
    } else if(uname.length<3){
        document.getElementById('userTip').textContent='用户名不少于3位';
        valid=false;
    }
    if(!email || !/\S+@\S+\.\S+/.test(email)){
        document.getElementById('emailTip').textContent='请输入正确的邮箱';
        valid=false;
    }
    if(pwd.length<6 || pwd.length>20){
        document.getElementById('pwdTip').textContent='密码6-20位';
        valid=false;
    }
    if(pwd!==cpwd){
        document.getElementById('cpwdTip').textContent='两次密码不一致';
        valid=false;
    }
    if(valid){
        alert("注册成功！（样例，不会实际提交）");
        // location.href="/login";
    }
}