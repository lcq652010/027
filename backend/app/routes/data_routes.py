from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import numpy as np
import json
import os
import uuid
from datetime import datetime
from ..database import get_db
from ..models import User, AnalysisRecord
from ..schemas import DataUploadResponse, DataCleaningResult
from ..auth import get_current_user
from ..config import settings
from ..data_service import data_cleaner, chart_generator

router = APIRouter(prefix="/data", tags=["数据处理"])

@router.post("/upload", response_model=DataUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 CSV 格式文件"
        )
    
    file_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = f"{file_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, original_filename)
    
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='gbk')
    
    return DataUploadResponse(
        message="文件上传成功",
        file_id=file_id,
        file_name=file.filename,
        rows_count=len(df),
        columns=list(df.columns)
    )

@router.post("/clean", response_model=DataCleaningResult)
async def clean_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 CSV 格式文件"
        )
    
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    original_rows = len(df)
    
    df_cleaned = data_cleaner.clean_data(df)
    
    cleaned_rows = len(df_cleaned)
    removed_rows = original_rows - cleaned_rows
    
    cleaned_filename = f"cleaned_{uuid.uuid4()}.csv"
    cleaned_path = os.path.join(settings.UPLOAD_DIR, cleaned_filename)
    df_cleaned.to_csv(cleaned_path, index=False, encoding='utf-8-sig')
    
    sample_data = df_cleaned.head(10).replace({np.nan: None}).to_dict(orient='records')
    
    os.remove(temp_path)
    
    return DataCleaningResult(
        original_rows=original_rows,
        cleaned_rows=cleaned_rows,
        removed_rows=removed_rows,
        columns=list(df_cleaned.columns),
        sample_data=sample_data
    )

@router.post("/analyze/line")
async def generate_line_chart(
    file: UploadFile = File(...),
    x_column: str = "Time",
    y_columns: str = "PM2.5,PM10,AQI",
    title: str = "空气质量趋势分析",
    current_user: User = Depends(get_current_user)
):
    y_cols = [y.strip() for y in y_columns.split(',')]
    
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    df_cleaned = data_cleaner.clean_data(df)
    
    chart_data = chart_generator.generate_line_chart_data(
        df_cleaned,
        x_column,
        y_cols,
        title
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/bar")
async def generate_bar_chart(
    file: UploadFile = File(...),
    x_column: str = "Time",
    y_columns: str = "PM2.5,PM10,AQI",
    title: str = "空气质量对比分析",
    aggregate: str = "mean",
    current_user: User = Depends(get_current_user)
):
    y_cols = [y.strip() for y in y_columns.split(',')]
    
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    df_cleaned = data_cleaner.clean_data(df)
    
    chart_data = chart_generator.generate_bar_chart_data(
        df_cleaned,
        x_column,
        y_cols,
        title,
        aggregate
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/statistics")
async def get_statistics(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    df_cleaned = data_cleaner.clean_data(df)
    
    statistics = chart_generator.generate_statistics_summary(df_cleaned)
    
    os.remove(temp_path)
    
    return statistics
