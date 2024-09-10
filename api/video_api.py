from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud.video_crud import get_all_videos
from db import get_db
from schemas.video_scheme import VideoResponse
from service.video_service import handle_video_upload, handle_video_download, handle_video_codec_check

router = APIRouter()


@router.put("/upload", response_model=list[VideoResponse])  # 1
async def upload_video(files: list[UploadFile], db: AsyncSession = Depends(get_db)):
    return await handle_video_upload(files, db)


@router.get("/download")  # 5, 조건에 맞게 구현되어 처리된 영상만 가능
async def download_video(video_id: int, db: AsyncSession = Depends(get_db)):
    return await handle_video_download(video_id, db)


@router.get("/view/all", response_model=list[VideoResponse])  # 6
async def view_processed_videos(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_all_videos(skip=skip, limit=limit, db=db)  # 그저 읽을 뿐이라 바로 crud


@router.get("/view/info") # 비디오 정보 확인용
async def view_video_codec(video_id: int, db: AsyncSession = Depends(get_db)):
    return await handle_video_codec_check(video_id,db)

