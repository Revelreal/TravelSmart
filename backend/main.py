if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app:app", host="localhost", port=8086, reload=True)