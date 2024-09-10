from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from api import video_api, job_api

app = FastAPI()

app.mount("/storage/origin", StaticFiles(directory="storage/origin"), name="origin_files")
app.mount("/storage/modi", StaticFiles(directory="storage/modi"), name="modi_files")

app.include_router(video_api.router, prefix="/video")
app.include_router(job_api.router, prefix="/video/process")
