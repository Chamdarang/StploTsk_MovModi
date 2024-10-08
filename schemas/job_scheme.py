from pydantic import BaseModel


class RequestBase(BaseModel):  # 요청 공통
    request_code: str


class TrimRequest(RequestBase):  # Trim
    video_id: int
    trim_start: str
    trim_end: str


class ConcatRequest(RequestBase):  # Concat
    video_ids: list[int]


class EncodingRequest(RequestBase):  # Encode
    video_id: int
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    resolution: str = "1920:1080"
    frame_rate: int = 30


class JobQueueCreate(BaseModel):
    job_type: str
    job_detail: dict
    output_path: str
    request_code: str