import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import local_processed_file_path, allowed_audio_codecs, allowed_video_codecs
from crud.job_crud import get_jobs_by_status_and_request_code, update_job_status, create_job
from crud.video_crud import get_video_by_id, \
    get_videos_by_ids, create_processed_video
from models.job_model import JobQueue
from schemas.job_scheme import TrimRequest, JobQueueCreate, ConcatRequest, EncodingRequest
from schemas.video_scheme import ProcessedVideoRequest
from utils.ffmpeg_util import trim_video, concat_videos, encode_video, get_media_info
from utils.time_util import is_float, time_to_seconds
from utils.video_util import get_file_path


async def handle_trim_request(request: TrimRequest, db: AsyncSession):
    ss_format1 = re.compile(r'^-?(\d{1,2}:)?[0-5]?\d:[0-5]?\d(\.\d+)?$')
    ss_format2 = re.compile(r'^-?\d+(\.\d+)?(s|ms|us)?$')
    to_format1 = re.compile(r'^(\d{1,2}:)?[0-5]?\d:[0-5]?\d(\.\d+)?$')
    to_format2 = re.compile(r'^\d+(\.\d+)?(s|ms|us)?$')
    request.trim_start = request.trim_start + "ms" if await is_float(request.trim_start) else request.trim_start
    request.trim_end = request.trim_end + "ms" if await is_float(request.trim_end) else request.trim_end

    if (not ss_format1.match(request.trim_start) and not ss_format2.match(request.trim_start)) or \
            (not to_format1.match(request.trim_end) and not to_format2.match(request.trim_end)):
        raise HTTPException(status_code=400, detail="Time format not supported")
    elif await time_to_seconds(request.trim_start) > await time_to_seconds(request.trim_end):
        raise HTTPException(status_code=400, detail="'trim_end' must be later than 'trim_start'")

    video = await get_video_by_id(db, request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video with id {request.video_id} not found.")


    # 작업 세부 사항 및 출력 파일 경로 설정
    job_detail = {
        "video_id": video.id,
        "trim_start": request.trim_start,
        "trim_end": request.trim_end
    }

    fn = await get_file_path(video)
    ext = fn.split(".")[-1].lower()
    fn = ".".join(fn.split(".")[:-1])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = local_processed_file_path + f"{fn.split('/')[-1]}_trim_{timestamp}.{ext}"

    # JobQueue 생성 및 데이터베이스에 추가
    job_data = JobQueueCreate(
        job_type="trim",
        job_detail=job_detail,
        output_path=output_path,
        request_code=request.request_code
    )
    job = await create_job(db=db, job_data=job_data)

    return {"message": "Trim job added to queue", "job_id": job.id}


async def handle_concat_request(request: ConcatRequest, db: AsyncSession):
    videos = await get_videos_by_ids(db, request.video_ids)
    if not videos or len(videos) != len(request.video_ids):
        raise HTTPException(status_code=404, detail="Some Videos not found")
    video_paths = [await get_file_path(video) for video in videos]
    video_codecs = [await get_media_info(path) for path in video_paths]
    video_codecs = [(x['video_streams'], x['audio_streams'], x['resolution'], x['frame_rate']) for x in video_codecs]
    if len(set(video_codecs)) != 1:
        raise HTTPException(status_code=400,
                            detail="All videos must have the same video codec, audio codec, resolution, and frame rate. Please ensure that the video files are consistent and try again.")
    job_detail = {"video_ids": request.video_ids}
    fn = video_paths[0].split("/")[-1]
    ext = fn.split(".")[-1].lower()
    fn = ".".join(fn.split(".")[:-1])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = local_processed_file_path + f"{fn}_concat_{timestamp}.{ext}"

    job = JobQueueCreate(
        job_type="concat",
        job_detail=job_detail,
        output_path=output_path,
        request_code=request.request_code
    )
    job = await create_job(db=db, job_data=job)

    return {"message": "Concat job added to queue", "job_id": job.id}


async def handle_encoding_request(request: EncodingRequest, db: AsyncSession):
    resolution_format = re.compile(r"^\d{1,}:\d{1,}$")

    if request.audio_codec not in allowed_audio_codecs or request.video_codec not in allowed_video_codecs:
        raise HTTPException(status_code=400,
                            detail="Unsupported codec requested. Please ensure that the video codec is one of the allowed formats: "
               f"{', '.join(allowed_video_codecs)} and the audio codec is one of the allowed formats: "
               f"{', '.join(allowed_audio_codecs)}.")
    elif not resolution_format.match(request.resolution):
        raise HTTPException(status_code=400, detail="Please provide a valid resolution.(e.g. '1920:1080')")
    video = await get_video_by_id(db, request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video with id {request.video_id} not found.")
    video_path = await get_file_path(video)
    video_info = await get_media_info(video_path)
    if video_info["video_streams"] == request.video_codec and video_info["audio_streams"] == request.audio_codec\
            and video_info["resolution"] == request.resolution and video_info["frame_rate"] == request.frame_rate:
        raise HTTPException(status_code=400,
                            detail="The video already matches the requested codec, resolution, and frame rate. No encoding is necessary")
    job_detail = {"video_id": request.video_id, "video_codec": request.video_codec, "audio_codec": request.audio_codec}
    fn = video_path.split("/")[-1]
    ext = fn.split(".")[-1].lower()
    fn = ".".join(fn.split(".")[:-1])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = local_processed_file_path + f"{fn}_encode_{timestamp}.{ext}"

    job = JobQueueCreate(
        job_type="encode",
        job_detail=job_detail,
        output_path=output_path,
        request_code=request.request_code
    )
    job = await create_job(db=db, job_data=job)

    return {"message": "Encode job added to queue", "job_id": job.id}


async def execute_pending_jobs(request, db: AsyncSession):
    jobs = await get_jobs_by_status_and_request_code(db, 0, request.request_code)

    if not jobs:
        raise HTTPException(status_code=400, detail=f"No pending jobs found for request_code: {request.request_code}")

    for job in jobs:
        try:
            if job.job_type == "trim":
                await handle_trim_job(job, db)
            elif job.job_type == "concat":
                await handle_concat_job(job, db)
            elif job.job_type == "encode":
                await handle_encode_job(job, db)
            await update_job_status(db, job, 1)

        except Exception as e:
            await update_job_status(db, job, 2)
            raise HTTPException(status_code=500, detail=f"Job {job.id} failed: {str(e)}")

    return {"message": f"All pending jobs for request_code {request.request_code} executed successfully"}


# 트림 작업 처리
async def handle_trim_job(job: JobQueue, db: AsyncSession):
    video = await get_video_by_id(db, job.job_detail["video_id"])
    video_path=await get_file_path(video)
    try:
        await trim_video(
            input_path=video_path,
            output_path=job.output_path,
            trim_start=job.job_detail["trim_start"],
            trim_end=job.job_detail["trim_end"]
        )
        video_data = ProcessedVideoRequest(processed_file_path=job.output_path, trim_info=job.job_detail)
        await create_processed_video(db=db, video=video_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")


async def handle_concat_job(job: JobQueue, db: AsyncSession):
    videos = await get_videos_by_ids(db, job.job_detail["video_ids"])
    video_paths = [await get_file_path(video) for video in videos]
    try:
        await concat_videos(
            video_list=video_paths,
            output_path=job.output_path
        )
        video_data = ProcessedVideoRequest(processed_file_path=job.output_path, concat_info=job.job_detail)
        await create_processed_video(db=db, video=video_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")


async def handle_encode_job(job: JobQueue, db: AsyncSession):
    video = await get_video_by_id(db, job.job_detail["video_id"])
    video_path = await get_file_path(video)
    try:
        await encode_video(
            input_file=video_path,
            output_file=job.output_path,
            video_codec=job.job_detail["video_codec"],
            audio_codec=job.job_detail["audio_codec"],
            resolution=job.job_detail["resolution"],
            frame_rate=job.job_detail["frame_rate"]
        )
        video_data = ProcessedVideoRequest(processed_file_path=job.output_path, encode_info=job.job_detail)
        await create_processed_video(db=db, video=video_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")
