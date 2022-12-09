from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/github/")
def github_webhook(payload: dict):
    print(payload)
    return {"message": "Hello World"}
