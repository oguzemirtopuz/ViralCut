import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/api/cut_raw")
async def cut_video_raw(
    request: Request,
    background_tasks: BackgroundTasks,
    start: float,
    end: float
):
    body = b"".join([chunk async for chunk in request.stream()])
    return {"message": "Success", "length": len(body)}

client = TestClient(app)

def test_fastapi_body():
    # Send post request with binary body
    res = client.post("/api/cut_raw?start=1.0&end=5.0", content=b"a" * 10)
    print("Response for correct query params, binary body:", res.status_code, res.json())

    # Send post request with JSON header?
    res2 = client.post("/api/cut_raw?start=1.0&end=5.0", content=b"a" * 10, headers={"Content-Type": "application/json"})
    print("Response for json header:", res2.status_code, res2.json())

if __name__ == "__main__":
    test_fastapi_body()
