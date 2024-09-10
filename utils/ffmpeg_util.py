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
        #'-c:v', "libx264",  # 일괄 인코딩 진행할 경우
        #'-c:a', "aac",  # 일괄 인코딩 진행할 경우
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


async def get_media_info(file_path: str):
    command = [
        'ffprobe',
        '-v', 'error',  # 오류 메시지만 출력
        '-show_entries', 'stream=codec_name,codec_type,width,height,r_frame_rate',  # 비디오와 오디오 정보 출력
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
    resolution = next((f"{s['width']}:{s['height']}" for s in media_info.get('streams', []) if s['codec_type'] == 'video'),None)
    frame_rate = next((s['r_frame_rate'] for s in media_info.get('streams', []) if s['codec_type'] == 'video'),None)

    # 프레임 레이트는 '30/1' 같은 형식으로 나올 수 있으므로, 이를 30같은 숫자로 변환
    if frame_rate and '/' in frame_rate:
        num, denom = frame_rate.split('/')
        frame_rate = int(float(num) / float(denom))

    return {
        "video_streams": video_streams,
        "audio_streams": audio_streams,
        "resolution": resolution,
        "frame_rate": frame_rate
    }


async def encode_video(input_file, output_file, video_codec, audio_codec,resolution,frame_rate):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', video_codec,
        '-c:a', audio_codec,
        '-vf', f"scale={resolution}",
        '-r', str(frame_rate),
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
