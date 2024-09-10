from sqlalchemy import Integer, Column, String, JSON, DateTime, func

from db import Base




class JobQueue(Base):
    __tablename__ = 'job_queue'
    id = Column(Integer, primary_key=True)
    request_code = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # trim, concat 등
    job_detail = Column(JSON, nullable=False)  # 작업의 세부 정보
    output_path = Column(String, nullable=False)  # 출력 경로
    status = Column(Integer, default=0)  # 작업 상태, 0 pending 1 success 2 fail
    created_at = Column(DateTime, default=func.now())  # 생성 시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())