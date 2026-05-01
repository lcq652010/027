import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from .config import settings

class DataCleaner:
    def __init__(self):
        self.common_air_columns = {
            'time', 'date', 'datetime', 'timestamp',
            'pm2.5', 'pm25', 'pm_25', 'pm2_5',
            'pm10', 'pm_10',
            'no2', 'no_2', 'nitrogen_dioxide',
            'so2', 'so_2', 'sulfur_dioxide',
            'co', 'carbon_monoxide',
            'o3', 'ozone',
            'aqi', 'air_quality_index',
            'temperature', 'temp',
            'humidity', 'hum',
            'pressure',
            'wind_speed', 'wind'
        }
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_cleaned = df.copy()
        
        df_cleaned = self._handle_missing_values(df_cleaned)
        
        df_cleaned = self._convert_data_types(df_cleaned)
        
        df_cleaned = self._remove_outliers(df_cleaned)
        
        df_cleaned = self._normalize_column_names(df_cleaned)
        
        return df_cleaned
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip().replace(' ', '_')
            if col_lower in ['pm2.5', 'pm25', 'pm_25', 'pm2_5']:
                column_mapping[col] = 'PM2.5'
            elif col_lower in ['pm10', 'pm_10']:
                column_mapping[col] = 'PM10'
            elif col_lower in ['no2', 'no_2', 'nitrogen_dioxide']:
                column_mapping[col] = 'NO2'
            elif col_lower in ['so2', 'so_2', 'sulfur_dioxide']:
                column_mapping[col] = 'SO2'
            elif col_lower in ['co', 'carbon_monoxide']:
                column_mapping[col] = 'CO'
            elif col_lower in ['o3', 'ozone']:
                column_mapping[col] = 'O3'
            elif col_lower in ['aqi', 'air_quality_index']:
                column_mapping[col] = 'AQI'
            elif col_lower in ['time', 'date', 'datetime', 'timestamp']:
                column_mapping[col] = 'Time'
            elif col_lower in ['temperature', 'temp']:
                column_mapping[col] = 'Temperature'
            elif col_lower in ['humidity', 'hum']:
                column_mapping[col] = 'Humidity'
            elif col_lower in ['pressure']:
                column_mapping[col] = 'Pressure'
            elif col_lower in ['wind_speed', 'wind']:
                column_mapping[col] = 'WindSpeed'
        
        return df.rename(columns=column_mapping)
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df_cleaned = df.copy()
        
        for col in df_cleaned.columns:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                median_value = df_cleaned[col].median()
                df_cleaned[col] = df_cleaned[col].fillna(median_value)
            elif pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
                df_cleaned = df_cleaned.dropna(subset=[col])
            else:
                df_cleaned[col] = df_cleaned[col].fillna('Unknown')
        
        return df_cleaned
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        df_cleaned = df.copy()
        
        for col in df_cleaned.columns:
            col_lower = col.lower()
            
            if any(time_key in col_lower for time_key in ['time', 'date', 'timestamp']):
                try:
                    df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
                except:
                    pass
            
            elif any(pollutant in col_lower for pollutant in ['pm', 'no2', 'so2', 'co', 'o3', 'aqi']):
                try:
                    df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
                except:
                    pass
        
        return df_cleaned
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        df_cleaned = df.copy()
        
        for col in df_cleaned.columns:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                col_lower = col.lower()
                
                if any(pollutant in col_lower for pollutant in ['pm', 'no2', 'so2', 'o3', 'aqi']):
                    Q1 = df_cleaned[col].quantile(0.25)
                    Q3 = df_cleaned[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    median_value = df_cleaned[col].median()
                    df_cleaned[col] = df_cleaned[col].apply(
                        lambda x: median_value if (pd.notna(x) and (x < lower_bound or x > upper_bound)) else x
                    )
        
        return df_cleaned

class ChartGenerator:
    def generate_line_chart_data(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "空气质量趋势分析"
    ) -> Dict[str, Any]:
        result = {
            "chart_type": "line",
            "title": title,
            "x_axis": [],
            "series": []
        }
        
        if x_column in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[x_column]):
                result["x_axis"] = df[x_column].dt.strftime('%Y-%m-%d %H:%M').tolist()
            else:
                result["x_axis"] = df[x_column].astype(str).tolist()
        
        for y_col in y_columns:
            if y_col in df.columns and pd.api.types.is_numeric_dtype(df[y_col]):
                series_data = {
                    "name": y_col,
                    "data": df[y_col].fillna(0).tolist(),
                    "type": "line"
                }
                result["series"].append(series_data)
        
        return result
    
    def generate_bar_chart_data(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "空气质量对比分析",
        aggregate: str = "mean"
    ) -> Dict[str, Any]:
        result = {
            "chart_type": "bar",
            "title": title,
            "x_axis": [],
            "series": []
        }
        
        if x_column in df.columns:
            if aggregate == "mean":
                grouped = df.groupby(x_column)[y_columns].mean()
            elif aggregate == "sum":
                grouped = df.groupby(x_column)[y_columns].sum()
            elif aggregate == "max":
                grouped = df.groupby(x_column)[y_columns].max()
            elif aggregate == "min":
                grouped = df.groupby(x_column)[y_columns].min()
            else:
                grouped = df.groupby(x_column)[y_columns].mean()
            
            if pd.api.types.is_datetime64_any_dtype(df[x_column]):
                result["x_axis"] = grouped.index.strftime('%Y-%m-%d').tolist()
            else:
                result["x_axis"] = grouped.index.astype(str).tolist()
            
            for y_col in y_columns:
                if y_col in grouped.columns:
                    series_data = {
                        "name": y_col,
                        "data": grouped[y_col].fillna(0).tolist(),
                        "type": "bar"
                    }
                    result["series"].append(series_data)
        
        return result
    
    def generate_statistics_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        summary = {
            "total_records": len(df),
            "columns": list(df.columns),
            "numeric_columns": [],
            "statistics": {}
        }
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                summary["numeric_columns"].append(col)
                col_stats = {
                    "mean": round(df[col].mean(), 2) if pd.notna(df[col].mean()) else None,
                    "median": round(df[col].median(), 2) if pd.notna(df[col].median()) else None,
                    "std": round(df[col].std(), 2) if pd.notna(df[col].std()) else None,
                    "min": round(df[col].min(), 2) if pd.notna(df[col].min()) else None,
                    "max": round(df[col].max(), 2) if pd.notna(df[col].max()) else None,
                    "missing_count": int(df[col].isna().sum())
                }
                summary["statistics"][col] = col_stats
        
        return summary

data_cleaner = DataCleaner()
chart_generator = ChartGenerator()
