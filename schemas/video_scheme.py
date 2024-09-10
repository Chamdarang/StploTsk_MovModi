from typing import Optional

from pydantic import BaseModel,model_validator


class UploadedVideoRequest(BaseModel):  # 업로드된 파일이 가질 데이터
    original_file_path: Optional[str] = None


class ProcessedVideoRequest(BaseModel):  # 생성된 파일이 가질 데이터
    processed_file_path: Optional[str] = None
    trim_info: Optional[dict] = None
    concat_info: Optional[dict] = None
    encode_info: Optional[dict] = None

    @model_validator(mode="before")
    def check_paths(cls, values):
        """
        세 info 중 하나는 반드시 내용이 있어야 함.
        다 비어 있으면 ValidationError 발생.
        """
        trim_info = values.get("trim_info")
        concat_info = values.get("concat_info")
        encode_info = values.get("encode_info")

        if not trim_info and not concat_info and not encode_info:
            raise ValueError("At least one of 'trim_info', 'concat_info', or 'encode_info' must be provided.")

        return values


class VideoResponse(UploadedVideoRequest, ProcessedVideoRequest):  # db에 기록되는 데이터, 위 2개 합쳐짐
    id: int

    class Config:
        from_attributes = True  # ORM 객체는 곧바로 JSON으로 다룰수 없어서 적용

    @model_validator(mode="before")
    def check_paths(cls, values):
        """
        original_file_path 또는 processed_file_path 중 하나는 반드시 내용이  있어야 함.
        둘 다 비어 있으면 ValidationError 발생.
        """
        original = values.original_file_path
        processed = values.processed_file_path

        if not original and not processed:
            raise ValueError("Either original_file_path or processed_file_path is required.")

        return values