if __name__ == "__main__":
    import uvicorn
    # 局域网内网都可以访问，但无法回环测试，请在防火墙放行端口
    # uvicorn.run("app.app:app", host="0.0.0.0", port=8086, reload=True)
    # 回环测试专用
    uvicorn.run("app.app:app", host="localhost", port=8086, reload=True)

