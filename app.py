import os
import subprocess
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(title="ViralCut Pro Backend")

# Allow CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_files(*file_paths):
    """Deletes temporary files after they have been sent."""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"Deleted temp file: {path}")
        except Exception as e:
            print(f"Error deleting file {path}: {e}")

from fastapi import Request

@app.post("/api/cut_raw")
async def cut_video_raw(
    request: Request,
    background_tasks: BackgroundTasks,
    start: float,
    end: float
):
    # Safety check
    if end <= start:
        return {"error": "End time must be greater than start time"}
    
    duration = end - start

    # On Windows, we must close the NamedTemporaryFile handle before other processes can use it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
        input_path = temp_input.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output:
        output_path = temp_output.name

    try:
        # Stream raw bytes to disk safely bypasses python-multipart bugs with huge files
        print(f"Receiving raw video stream into {input_path}...")
        with open(input_path, "wb") as buffer:
            async for chunk in request.stream():
                buffer.write(chunk)
            
        print(f"Stream saved. Cutting from {start} for {duration} seconds...")

        command = [
            "ffmpeg",
            "-y",                # Overwrite output
            "-nostdin",          # Prevent hanging waiting for input
            "-ss", str(start),   # Start time
            "-i", input_path,    # Input file
            "-t", str(duration), # Duration to cut
            "-c", "copy",        # Stream copy (no re-encode)
            "-avoid_negative_ts", "make_zero",
            output_path          # Output file
        ]
        
        # Adding timeout to prevent infinite hang
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        
        if process.returncode != 0:
            print(f"FFmpeg Error:\n{process.stderr}")
            cleanup_files(input_path, output_path)
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Kesim işlemi başarısız. FFmpeg Hatası: {process.stderr[-200:]}")

        print("FFmpeg process completed successfully.")

        # Schedule cleanup
        background_tasks.add_task(cleanup_files, input_path, output_path)

        return FileResponse(
            path=output_path, 
            filename=f"ViralCut_{start}s-{end}s.mp4",
            media_type="video/mp4"
        )
        
    except subprocess.TimeoutExpired:
        cleanup_files(input_path, output_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=504, detail="İşlem zaman aşımına uğradı (Video çok büyük olabilir).")
    except HTTPException:
        raise
    except Exception as e:
        cleanup_files(input_path, output_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
