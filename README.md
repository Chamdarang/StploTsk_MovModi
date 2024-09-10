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
※ Trim작업과 Concat작업은 '사용자가 업로드 한 영상' 외에도 '생성된 최종 동영상'에도 수행할 수 있도록 진행함<br>
※ Concat작업에서 일괄적으로 코덱을 맞추는 인코딩을 진행하면 시간이 오래걸리는 이유로 별도의 Encode API를 만들어 코덱을 변환해야 하도록 함<br>
  Encode API 없이 Concat에서 일괄적으로 인코딩 하도록 하려면<br>
  `service.job_service.py`의 `handle_concat_request()`에 해당하는 67\~72줄을 주석처리/삭제 후<br>
  `utils.ffmpeg_util.py`의 `concat_videos()`에 해당하는 38\~41줄의 주석처리를 해제<br>
※ API 문서는 `API 가이드 문서.pdf` 혹은 서비스 실행 후 `서비스주소/docs`의 Swagger 문서 참고<br>



-   
URI : 
Method :  
Request : 
Response :
Note :
