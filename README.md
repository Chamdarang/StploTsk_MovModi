## 프로젝트 구조

app
 - api 
   - video_api.py - 업로드, 다운로드 등 비디오 관련 API 엔드포인트
   - job_api.py - Trim, Concat 등 편집작업 관련 API 엔드포인트
 - crud 
   - video_crud.py - 비디오 관련 DB 조작 함수
   - job_crud.py - 편집작업 관련 DB 조작 함수
 - models
   - video_model.py - 비디오 테이블 모델 정의
   - job_model.py - 편집작업(대기열) 테이블 모델 정의
 - schemas
   - video_scheme.py 비디오 관련 스키마 정의
   - job_scheme.py 편집작업 관련 스키마 정의
 - storage
   - modi 생성된 영상이 저장되는 폴더
   - origin 업로드된 영상이 저장되는 폴더
 - service
   - video_service.py 비디오 관련 로직
   - job_service.py 영상처리 관련 로직
 - utils
   - ffmpeg_util.py FFmpeg 명령어를 수행하는 유틸 함수
   - time_util.py 시간 형식 관련 유틸 함수
   - video_util.py 비디오 관련 유틸 함수
 - config.py 서비스 환경 구성 정보
 - db.py - DB설정
 - main.py - FastAPI 시작 및 라우터
 - requirmets.txt 사용된 패키지 목록, `pip install -r requirements.txt` 명령어로 해당 패키지 설치

---
## 개발환경
파이썬 버전: 3.10.11  
사용 DB: PostgreSQL  
json타입 저장을 위해 채택함

테이블간의 관계성이 존재하지 않도록 설계되었기에 json타입으로 저장되는것이 기본인 NoSQL을 사용하는것도 고려해보았으나<br>
Python(FastAPI)+PostgreSQL 환경이 상대적으로 익숙하였고, RDB의 제약조건 기능을 활용하기 위해 채택함


## 설치방법
0. Python 3.10 버전 설치
1. `pip install -r requirements.txt` 필요 패키지 설치
2. config.py에서 db 접속정보 설정<br>
   기본적으로 `postgres`라는 사용자가 `root`라는 패스워드로 `localhost`상 DB서버의 `movmodi` 데이터베이스에 접속하도록 되어 있음.
3. 아래의 기재된 DDL을 참고하여 데이터를 저장하기 위한 테이블을 생성
4. 루트 디렉토리에서 'uvicorn main:app'으로 실행

videos 테이블 DDL
```
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    trim_info JSONB,
    concat_info JSONB,
    original_file_path VARCHAR,
    processed_file_path VARCHAR,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    encode_info JSONB,
    CONSTRAINT chk_file_paths CHECK (
        original_file_path IS NOT NULL OR processed_file_path IS NOT NULL
    )
);
```
job_queue 테이블 DDL
```
CREATE TABLE job_queue (
    id SERIAL PRIMARY KEY,
    request_code VARCHAR NOT NULL,
    job_type VARCHAR NOT NULL,
    job_detail JSONB NOT NULL,
    output_path VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## API
※비고1- API 문서는 `API 가이드 문서.pdf` 혹은 서비스 실행 후 `서비스주소/docs`의 Swagger 문서 참고<br>
※비고2- Trim작업과 Concat작업은 '사용자가 업로드 한 영상' 외에도 '생성된 최종 동영상'에도 수행할 수 있도록 진행함<br>
※비고3- Concat작업에서 일괄적으로 코덱을 맞추는 인코딩을 진행하면 시간이 오래걸리는 이유로 별도의 Encode API를 만들어 코덱을 변환해야 하도록 함<br>
  Encode API 없이 Concat에서 일괄적으로 인코딩 하도록 하려면<br>
  `service.job_service.py`의 `handle_concat_request()`에 해당하는 67\~72줄을 주석처리/삭제 후<br>
  `utils.ffmpeg_util.py`의 `concat_videos()`에 해당하는 38\~41줄의 주석처리를 해제<br>




- 파일 업로드<br>
URI : /video/uploade<br>
Method : put<br>
Request : files: List[Files]<br>
Note :<br>
  - response_body에 담는것이 아니라 `response = requests.put(url, files=files)`처럼 별도로 보내는것임<br>
  - 10가지의 일반적인 비디오파일 형식을 허용하도록 진행함<br>
  - 유저가 업로드한 파일명을 남겨두면서 중복이 없도록 하기 위해 파일명에 연월일시분초를 추가<br>
  - 하나만 보내도 되나 안 보내는것은 안됨<br>


- 파일 다운로드<br>
URI : /video/download<br>
Method : get<br>
Request : /video/download?video_id=1<br>
Note :<br>
  - 요구사항에 따라 작업이 완료된 최종 동영상에 한하여 지원하도록 함<br>
  - 로컬서버에서 진행하여 `http://127.0.0.1:8000`라는 주소값이 하드코딩 됨<br>


- 전체 파일 목록 확인<br>
URI : /video/view/all<br>
Method : get<br>
Request : /video/view/all?skip=0&limit=100<br>
Note :<br>
  - 페이징을 위한 skip과 limit는 보내지 않아도 됨(기본적으로 0페이지, 100개 제한으로 보내줌)<br>
  - 각 항목이 5개의 정보를 다 가지고 있어야 한다는 조건에 따라 구현됨<br>


- 파일 정보 확인<br>
URI : /video/view/info<br>
Method : get<br>
Request : /video/view/all?video_id=1<br>
Note :<br>
  - 추가로 구현된 인코딩 작업 관련하여 파일의 코덱, 프레임, 해상도를 확인하기 위해 구현함<br>


- Trim 작업 예약<br>
URI : /video/process/trim<br>
Method : post<br>
Request : { "request_code":str, "video_id":int, "trim_start":str, "trim_end":str }<br>
Note :<br>
  - 작업 수행 단계에서의 사용자 구분을 위한 request_code 추가<br>
  - 요청값에 대한 검증 진행 후 작업대기열에 추가하도록 진행<br>
  - `형식 또는 밀리초`라는 요구사항에 대해 FFmpeg에서 지원하는 2가지 형식 외에 숫자만 올 경우 밀리초로 인식하도록 하는것으로 이해함<br>
  - trim_end에는 음수 시간값이 불가능하도록 구현<br>


- Concat 작업 예약<br>
URI : /video/process/concat<br>
Method : post<br>
Request : { "request_code":str, "video_ids":List[int] }<br>
Note :<br>
  - 작업 수행 단계에서의 사용자 구분을 위한 request_code 추가<br>
  - 요청값에 대한 검증 진행 후 작업대기열에 추가하도록 진행<br>
  - 인코딩을 하며 concat을 하면 오래걸리는 이유로 비디오 정보(코덱,해상도,프레임)가 일치해야 가능하도록 구현함<br>
    해당 내용 관련하여 원치 않을 시 상단 비고3 참고<br>


- Encoding 작업 예약<br>
URI : /video/process/encodeing<br>
Method : post<br>
Request : { "request_code":str, "video_ids":int, "video_codec":str, "audio_codec":str, "resolution":str, "frame_rate":int }<br>
Note :<br>
  - concat작업의 속도를 위해 따로 구현함<br>
  - video_codec, audio_codec, resolution, frame_rate 각 정보는 보내지 않아도 되며<br>
    보내지 않을 시 각각 "libx264", "aac", "1920:1080", 30 으로 전달되도록 함<br>
  - 본 작업 또한 작업대기열에 추가되어 명령 작업 수행시 진행되도록 함<br>


- 예약된 작업 수행<br>
URI : /video/process/execute<br>
Method : post<br>
Request : { "request_code":str }<br>
Note :<br>
  - 동일한 request_code 예약된 대기중인 작업을 순차적으로 수행함<br>
  - 파일명에 작업명(trim,concat,encode)와 시간(연월일시분초)를 추가하여 중복되지 않도록 저장<br>
  - 작업을 수행하지 않으면 파일도 생성되지 않고 작업 결과도 알 수 없는 상태이기에<br>
    예약된 작업의 결과를 다음 concat 작업에 이어서 사용하는 등의 활용은 되지 않도록 함 ( `concat( trim(video), video )` 불가)
