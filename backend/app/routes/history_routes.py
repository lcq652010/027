from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime
import json
from ..database import get_db
from ..models import User, AnalysisRecord, UserRole
from ..schemas import (
    AnalysisRecordCreate,
    AnalysisRecordResponse,
    AnalysisRecordDetail
)
from ..auth import get_current_user, check_user_permission

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
    search: Optional[str] = Query(None, description="搜索关键词（文件名）"),
    chart_type: Optional[str] = Query(None, description="图表类型筛选"),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方式: asc/desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisRecord)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AnalysisRecord.user_id == current_user.id)
    
    if search:
        query = query.filter(
            or_(
                AnalysisRecord.file_name.ilike(f"%{search}%"),
                AnalysisRecord.analysis_type.ilike(f"%{search}%")
            )
        )
    
    if chart_type:
        query = query.filter(AnalysisRecord.chart_type == chart_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AnalysisRecord.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(AnalysisRecord.created_at <= date_to_obj)
        except ValueError:
            pass
    
    sort_column = getattr(AnalysisRecord, sort_by, AnalysisRecord.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    records = query.offset(skip).limit(limit).all()
    
    return records

@router.get("/count")
def get_history_count(
    search: Optional[str] = Query(None),
    chart_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisRecord)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AnalysisRecord.user_id == current_user.id)
    
    if search:
        query = query.filter(
            or_(
                AnalysisRecord.file_name.ilike(f"%{search}%"),
                AnalysisRecord.analysis_type.ilike(f"%{search}%")
            )
        )
    
    if chart_type:
        query = query.filter(AnalysisRecord.chart_type == chart_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AnalysisRecord.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(AnalysisRecord.created_at <= date_to_obj)
        except ValueError:
            pass
    
    count = query.count()
    
    return {"count": count}

@router.get("/{record_id}", response_model=AnalysisRecordDetail)
def get_record_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    if not check_user_permission(current_user, record.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此记录"
        )
    
    return record

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    if not check_user_permission(current_user, record.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此记录"
        )
    
    db.delete(record)
    db.commit()

@router.post("/batch-delete", status_code=status.HTTP_200_OK)
def batch_delete_records(
    record_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not record_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未提供记录ID"
        )
    
    records = db.query(AnalysisRecord).filter(
        AnalysisRecord.id.in_(record_ids)
    ).all()
    
    if current_user.role != UserRole.ADMIN:
        for record in records:
            if record.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"无权删除记录 {record.id}"
                )
    
    deleted_count = len(records)
    
    for record in records:
        db.delete(record)
    
    db.commit()
    
    return {
        "message": f"成功删除 {deleted_count} 条记录",
        "deleted_count": deleted_count
    }

@router.get("/statistics/summary")
def get_history_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisRecord)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AnalysisRecord.user_id == current_user.id)
    
    total_records = query.count()
    
    chart_type_stats = {}
    chart_types = ["line", "bar", "scatter", "area", "pie", "heatmap"]
    for ct in chart_types:
        count = query.filter(AnalysisRecord.chart_type == ct).count()
        if count > 0:
            chart_type_stats[ct] = count
    
    recent_records = query.order_by(
        AnalysisRecord.created_at.desc()
    ).limit(10).all()
    
    return {
        "total_records": total_records,
        "chart_type_distribution": chart_type_stats,
        "recent_records": [
            {
                "id": r.id,
                "file_name": r.file_name,
                "chart_type": r.chart_type,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_records
        ]
    }

@router.get("/statistics/chart-types")
def get_chart_type_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    
    query = db.query(
        AnalysisRecord.chart_type,
        func.count(AnalysisRecord.id).label('count')
    )
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AnalysisRecord.user_id == current_user.id)
    
    results = query.group_by(AnalysisRecord.chart_type).all()
    
    return {
        "chart_types": [
            {"chart_type": r.chart_type, "count": r.count}
            for r in results
        ]
    }
