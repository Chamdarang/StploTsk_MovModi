from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from models.video_model import Videos
from schemas.video_scheme import UploadedVideoRequest, ProcessedVideoRequest


async def get_all_videos(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Videos).offset(skip).limit(limit))
    videos = result.scalars().all()
    return videos


async def get_video_by_id(db: AsyncSession, video_id: int):
    result = await db.execute(select(Videos).filter(Videos.id == video_id))
    return result.scalars().first()


async def get_videos_by_ids(db: AsyncSession, video_ids: list[int]):
    query = select(Videos).filter(Videos.id.in_(video_ids))
    result = await db.execute(query)
    return result.scalars().all()


async def get_processed_video_by_id(db: AsyncSession, video_id: int):
    result = await db.execute(
        select(Videos).filter(Videos.id == video_id, Videos.processed_file_path.isnot(None))
    )
    videos = result.scalars().first()
    return videos

async def create_uploaded_video(db: AsyncSession, video: UploadedVideoRequest):
    try:
        db_video = Videos(**video.dict())
        db.add(db_video)  # 비동기도 await 안붙고 그대로
        await db.commit()
        await db.refresh(db_video)
        return db_video
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error: unable to save video.")


async def create_processed_video(db: AsyncSession, video: ProcessedVideoRequest):
    try:
        db_video = Videos(**video.dict())
        db.add(db_video)
        await db.commit()
        await db.refresh(db_video)
        return db_video
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error: unable to save video.")
