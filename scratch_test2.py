import asyncio
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/api/cut_raw")
async def cut_video_raw(
    request: Request,
    start: float,
    end: float
):
    try:
        body = b"".join([chunk async for chunk in request.stream()])
        return {"message": "Success", "length": len(body)}
    except Exception as e:
        return {"detail": str(e)}

client = TestClient(app)

def test_fastapi_body():
    # Send post request with binary body
    res = client.post("/api/cut_raw?start=1.0&end=5.0", content=b"a" * 10)
    print("Response for binary:", res.json())

    # Send post request with malformed JSON
    res2 = client.post("/api/cut_raw?start=1.0&end=5.0", content=b"{malformed json", headers={"Content-Type": "application/json"})
    print("Response for malformed JSON:", res2.status_code, res.json())

    # Send FormData
    files = {'file': ('test.mp4', b'test content', 'video/mp4')}
    res3 = client.post("/api/cut_raw?start=1.0&end=5.0", files=files)
    print("Response for FormData:", res3.status_code, res3.json())

if __name__ == "__main__":
    test_fastapi_body()
