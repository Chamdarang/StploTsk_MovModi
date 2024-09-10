import asyncio
from json import loads

from fastapi import HTTPException


async def trim_video(input_path: str, output_path: str, trim_start: str, trim_end: str):
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', trim_start,
        '-to', trim_end,
        output_path
    ]

    process = await asyncio.create_subprocess_exec(  # 별도의 프로세스 생성해서 실행, 생성된 프로세스 정보 받아옴
        *command,
        stdout=asyncio.subprocess.PIPE, # 출력 담기는 스트림
        stderr=asyncio.subprocess.PIPE  # 에러 담기는 스트림
    )

    stdout, stderr = await process.communicate() # 끝나고 담겨있는 스트림 받아오기

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Trim failed: {stderr.decode()}")


async def concat_videos(video_list: list, output_path: str):
    with open('filelist.txt', 'w', encoding="utf-8") as f:
        for video in video_list:
            f.write(f"file '{video}'\n")

    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'filelist.txt',
        output_path
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Concat failed: {stderr.decode()}")


async def get_media_codec(file_path: str):
    command = [
        'ffprobe',
        '-v', 'error',  # 오류 메시지만 출력
        '-show_entries', 'stream=codec_name,codec_type',  # 비디오와 오디오 정보 출력
        '-of', 'json',  # 결과를 JSON 형식으로 출력
        file_path
    ]

    # 비동기로 서브프로세스 실행
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # 프로세스의 stdout, stderr 읽기
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Probe failed: {stderr.decode()}")

    # JSON 형식의 정보를 반환
    media_info = loads(stdout.decode('utf-8'))

    video_streams = next((s['codec_name'] for s in media_info.get('streams', []) if s['codec_type'] == 'video'), None)  #  type이 "video"인 dict의 name을 가져오는데 없으면 none
    audio_streams = next((s['codec_name'] for s in media_info.get('streams', []) if s['codec_type'] == 'audio'), None)

    return {
        "video_streams": video_streams,
        "audio_streams": audio_streams
    }


async def encode_video(input_file, output_file, video_codec, audio_codec):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', video_codec,
        '-c:a', audio_codec,
        output_file
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Encode failed: {stderr.decode()}")
