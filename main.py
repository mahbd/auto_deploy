from fastapi import FastAPI
import json

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/github/")
def github_webhook(payload: dict):
    json_string = json.dumps(payload)
    print(json_string)
    return {"message": "Hello World"}
