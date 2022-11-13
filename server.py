import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

from camera import *


app = FastAPI()


@app.get('/', response_class=HTMLResponse)
async def video_stream():
    return StreamingResponse(
        stream_generator(Camera(source=from_webcam)),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
