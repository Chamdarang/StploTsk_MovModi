from schemas.video_scheme import VideoResponse


async def get_file_path(video: VideoResponse):
    return video.original_file_path or video.processed_file_path  # 둘중 있는거를 리턴
