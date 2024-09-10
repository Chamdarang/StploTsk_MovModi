from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.job_scheme import TrimRequest, ConcatRequest, RequestBase, EncodingRequest
from service.job_service import execute_pending_jobs, handle_trim_request, handle_concat_request, \
    handle_encoding_request

router = APIRouter()


@router.post("/trim")  # 2
async def add_trim_request(request: TrimRequest, db: AsyncSession = Depends(get_db)):
    return await handle_trim_request(request, db)


@router.post("/concat")  # 3
async def add_concat_request(request: ConcatRequest, db: AsyncSession = Depends(get_db)):
    return await handle_concat_request(request, db)


@router.post("/encoding")  # 코덱,해상도,프레임 바꿔 재인코딩
async def encode_request(request: EncodingRequest, db: AsyncSession = Depends(get_db)):
    return await handle_encoding_request(request, db)


@router.post("/execute")  # 4
async def execute_request(request: RequestBase, db: AsyncSession = Depends(get_db)):
    return await execute_pending_jobs(request, db)

