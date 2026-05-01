from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from ..database import get_db
from ..models import User, AnalysisRecord
from ..schemas import (
    AnalysisRecordCreate,
    AnalysisRecordResponse,
    AnalysisRecordDetail
)
from ..auth import get_current_user

router = APIRouter(prefix="/history", tags=["历史记录"])

@router.post("/save", response_model=AnalysisRecordResponse)
def save_analysis_record(
    record_data: AnalysisRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_record = AnalysisRecord(
        user_id=current_user.id,
        file_name=record_data.file_name,
        original_file_path="",
        analysis_type=record_data.analysis_type,
        chart_type=record_data.chart_type or "line",
        chart_data=record_data.chart_data,
        analysis_config=record_data.analysis_config
    )
    
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return new_record

@router.get("/list", response_model=List[AnalysisRecordResponse])
def get_user_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == current_user.id
    ).order_by(
        AnalysisRecord.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return records

@router.get("/{record_id}", response_model=AnalysisRecordDetail)
def get_record_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    return record

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    db.delete(record)
    db.commit()

@router.get("/statistics/summary")
def get_history_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_records = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == current_user.id
    ).count()
    
    line_chart_count = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == current_user.id,
        AnalysisRecord.chart_type == "line"
    ).count()
    
    bar_chart_count = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == current_user.id,
        AnalysisRecord.chart_type == "bar"
    ).count()
    
    return {
        "total_records": total_records,
        "line_chart_count": line_chart_count,
        "bar_chart_count": bar_chart_count
    }
