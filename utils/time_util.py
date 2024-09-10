async def is_float(val: str):  # 문자열이 숫자형태인지 확인
    try:
        float(val)
        return True
    except ValueError:
        return False


async def time_to_seconds(time_str: str) -> float:  # 문자열 시간을 초(sec) 단위의 숫자로 바꿈
    if "s" in time_str:
        # 초 또는 밀리초, 마이크로초 형식
        if "ms" in time_str:
            return float(time_str.replace("ms", "")) / 1000.0
        elif "us" in time_str:
            return float(time_str.replace("us", "")) / 1000000.0
        else:
            return float(time_str.replace("s", ""))
    else:
        # HH:MM:SS 형식 처리
        parts = time_str.split(':')
        parts = [float(part) for part in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        else:
            return parts[0]