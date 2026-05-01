from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Query
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
    
    validation = data_cleaner.validate_data(df)
    
    return DataUploadResponse(
        message="文件上传成功",
        file_id=file_id,
        file_name=file.filename,
        rows_count=len(df),
        columns=list(df.columns)
    )

@router.post("/clean")
async def clean_data(
    file: UploadFile = File(...),
    missing_strategy: str = Form("median"),
    outlier_method: str = Form("iqr"),
    remove_duplicates: bool = Form(True),
    constant_value: float = Form(0.0),
    outlier_threshold: float = Form(1.5),
    zscore_threshold: float = Form(3.0),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 CSV 格式文件"
        )
    
    valid_missing_strategies = ["mean", "median", "mode", "ffill", "bfill", "drop", "constant"]
    valid_outlier_methods = ["iqr", "zscore", "none"]
    
    if missing_strategy not in valid_missing_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的缺失值处理策略，可选值: {valid_missing_strategies}"
        )
    
    if outlier_method not in valid_outlier_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的异常值处理方法，可选值: {valid_outlier_methods}"
        )
    
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    validation = data_cleaner.validate_data(df)
    
    original_rows = len(df)
    
    df_cleaned, report = data_cleaner.clean_data(
        df,
        missing_strategy=missing_strategy,
        outlier_method=outlier_method,
        remove_duplicates=remove_duplicates,
        constant_value=constant_value,
        outlier_threshold=outlier_threshold,
        zscore_threshold=zscore_threshold
    )
    
    cleaned_rows = len(df_cleaned)
    removed_rows = original_rows - cleaned_rows
    
    cleaned_filename = f"cleaned_{uuid.uuid4()}.csv"
    cleaned_path = os.path.join(settings.UPLOAD_DIR, cleaned_filename)
    df_cleaned.to_csv(cleaned_path, index=False, encoding='utf-8-sig')
    
    sample_data = df_cleaned.head(10).replace({np.nan: None}).to_dict(orient='records')
    
    os.remove(temp_path)
    
    return {
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "removed_rows": removed_rows,
        "columns": list(df_cleaned.columns),
        "sample_data": sample_data,
        "validation": validation,
        "cleaning_report": report.to_dict()
    }

@router.post("/validate")
async def validate_data(
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
    
    validation = data_cleaner.validate_data(df)
    statistics = chart_generator.generate_statistics_summary(df)
    
    os.remove(temp_path)
    
    return {
        "validation": validation,
        "statistics": statistics
    }

@router.post("/analyze")
async def generate_chart(
    file: UploadFile = File(...),
    chart_type: str = Form("line"),
    x_column: str = Form("Time"),
    y_columns: str = Form("PM2.5,PM10,AQI"),
    title: str = Form("数据分析"),
    aggregate: str = Form("mean"),
    stack: bool = Form(False),
    smooth: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    valid_chart_types = ["line", "bar", "scatter", "area", "pie", "heatmap"]
    
    if chart_type not in valid_chart_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的图表类型，可选值: {valid_chart_types}"
        )
    
    y_cols = [y.strip() for y in y_columns.split(',')]
    
    content = await file.read()
    
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.csv")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_path, encoding='gbk')
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator.generate_chart_data(
        df_cleaned,
        chart_type=chart_type,
        x_column=x_column,
        y_columns=y_cols,
        title=title,
        aggregate=aggregate,
        stack=stack,
        smooth=smooth
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/line")
async def generate_line_chart(
    file: UploadFile = File(...),
    x_column: str = Query("Time"),
    y_columns: str = Query("PM2.5,PM10,AQI"),
    title: str = Query("空气质量趋势分析"),
    smooth: bool = Query(True),
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
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator._generate_line_chart(
        df_cleaned,
        x_column,
        y_cols,
        title,
        smooth=smooth
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/bar")
async def generate_bar_chart(
    file: UploadFile = File(...),
    x_column: str = Query("Time"),
    y_columns: str = Query("PM2.5,PM10,AQI"),
    title: str = Query("空气质量对比分析"),
    aggregate: str = Query("mean"),
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
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator._generate_bar_chart(
        df_cleaned,
        x_column,
        y_cols,
        title,
        aggregate=aggregate
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/scatter")
async def generate_scatter_chart(
    file: UploadFile = File(...),
    x_column: str = Query("Time"),
    y_columns: str = Query("PM2.5,PM10,AQI"),
    title: str = Query("散点图分析"),
    symbol_size: int = Query(8),
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
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator._generate_scatter_chart(
        df_cleaned,
        x_column,
        y_cols,
        title,
        symbol_size=symbol_size
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/area")
async def generate_area_chart(
    file: UploadFile = File(...),
    x_column: str = Query("Time"),
    y_columns: str = Query("PM2.5,PM10,AQI"),
    title: str = Query("面积图分析"),
    stack: bool = Query(False),
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
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator._generate_area_chart(
        df_cleaned,
        x_column,
        y_cols,
        title,
        stack=stack
    )
    
    os.remove(temp_path)
    
    return chart_data

@router.post("/analyze/pie")
async def generate_pie_chart(
    file: UploadFile = File(...),
    x_column: str = Query("Time"),
    y_columns: str = Query("PM2.5"),
    title: str = Query("占比分析"),
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
    
    df_cleaned, _ = data_cleaner.clean_data(df)
    
    chart_data = chart_generator._generate_pie_chart(
        df_cleaned,
        x_column,
        y_cols,
        title
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
    
    statistics = chart_generator.generate_statistics_summary(df)
    
    os.remove(temp_path)
    
    return statistics
