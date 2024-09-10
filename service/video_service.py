from datetime import datetime

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import local_origin_file_path, allowed_media_types
from crud.video_crud import create_uploaded_video, get_processed_video_by_id, get_video_by_id
from schemas.video_scheme import UploadedVideoRequest
from utils.ffmpeg_util import get_media_info


async def handle_video_upload(files: list[UploadFile], db: AsyncSession):
    path = local_origin_file_path
    uploaded_videos = []

    if not files:
        raise HTTPException(status_code=400, detail="There are no files selected")

    for file in files:
        fn = file.filename
        ext = fn.split(".")[-1].lower()
        if ext not in allowed_media_types:
            raise HTTPException(status_code=415, detail=f"{fn} has an unsupported format.")

    for file in files:
        content = await file.read()
        fn = file.filename
        ext = fn.split(".")[-1].lower()
        fn = ".".join(fn.split(".")[:-1])
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_fn = f"{fn}_{timestamp}.{ext}"

        with open(path + unique_fn, "wb") as f:
            f.write(content)

        video_data = UploadedVideoRequest(original_file_path=path + unique_fn)
        saved_video = await create_uploaded_video(db=db, video=video_data)
        uploaded_videos.append(saved_video)

    return uploaded_videos


async def handle_video_download(video_id: int, db: AsyncSession):
    video = await get_processed_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Processed video not found.")

    return {"download_link": f"http://127.0.0.1:8000{video.processed_file_path[1:]}"}


async def handle_video_codec_check(video_id: int, db: AsyncSession):
    video = await get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return await get_media_info(video.original_file_path)
