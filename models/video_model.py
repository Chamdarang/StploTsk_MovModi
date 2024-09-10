from sqlalchemy import Column, Integer, String, DateTime, func, JSON, CheckConstraint
from db import Base



class Videos(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    trim_info = Column(JSON, nullable=True)
    concat_info = Column(JSON, nullable=True)
    encode_info = Column(JSON, nullable=True)
    original_file_path = Column(String, nullable=True)
    processed_file_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=func.now())


    __table_args__ = (
        CheckConstraint(
            "(original_file_path IS NOT NULL OR processed_file_path IS NOT NULL)",
            name="chk_file_paths"
        ),
    )

