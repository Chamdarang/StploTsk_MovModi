from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_model import JobQueue
from schemas.job_scheme import JobQueueCreate


async def get_jobs_by_status_and_request_code(db: AsyncSession, status_code:int, request_code: str):
    query = select(JobQueue).filter(JobQueue.status == status_code, JobQueue.request_code == request_code)
    result = await db.execute(query)
    return result.scalars().all()


async def create_job(db: AsyncSession, job_data: JobQueueCreate):
    try:
        job = JobQueue(**job_data.dict())
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: unable to create job. {str(e)}")


async def update_job_status(db: AsyncSession, job: JobQueue, status: int):
    try:
        job.status = status
        db.add(job)  # 상태 변경된 객체 추가 (비동기 세션에서는 add가 필요할 수 있음)
        await db.commit()  # 비동기 커밋
        await db.refresh(job)  # 커밋 후 객체 갱신
        return job
    except SQLAlchemyError as e:
        await db.rollback()  # 오류 발생 시 롤백
        raise HTTPException(status_code=500, detail=f"Database error: unable to update job status. {str(e)}")