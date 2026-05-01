import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
from .config import settings

class CleaningReport:
    def __init__(self):
        self.steps = []
        self.original_rows = 0
        self.original_columns = 0
        self.final_rows = 0
        self.final_columns = 0
        self.missing_values_before = {}
        self.missing_values_after = {}
        self.outliers_removed = {}
        self.duplicates_removed = 0
        self.data_type_changes = {}
    
    def add_step(self, step_name: str, description: str, rows_before: int, rows_after: int):
        self.steps.append({
            "step": step_name,
            "description": description,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_changed": rows_after - rows_before
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_shape": {
                "rows": self.original_rows,
                "columns": self.original_columns
            },
            "final_shape": {
                "rows": self.final_rows,
                "columns": self.final_columns
            },
            "rows_removed": self.original_rows - self.final_rows,
            "steps": self.steps,
            "missing_values_before": self.missing_values_before,
            "missing_values_after": self.missing_values_after,
            "outliers_removed": self.outliers_removed,
            "duplicates_removed": self.duplicates_removed,
            "data_type_changes": self.data_type_changes
        }

class AdvancedDataCleaner:
    MISSING_STRATEGY_MEAN = "mean"
    MISSING_STRATEGY_MEDIAN = "median"
    MISSING_STRATEGY_MODE = "mode"
    MISSING_STRATEGY_FFILL = "ffill"
    MISSING_STRATEGY_BFILL = "bfill"
    MISSING_STRATEGY_DROP = "drop"
    MISSING_STRATEGY_CONSTANT = "constant"
    
    OUTLIER_METHOD_IQR = "iqr"
    OUTLIER_METHOD_ZSCORE = "zscore"
    OUTLIER_METHOD_NONE = "none"
    
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
        
        self.column_mappings = {
            'pm2.5': ['pm2.5', 'pm25', 'pm_25', 'pm2_5', 'pm 2.5'],
            'PM10': ['pm10', 'pm_10', 'pm 10'],
            'NO2': ['no2', 'no_2', 'nitrogen_dioxide', 'no 2'],
            'SO2': ['so2', 'so_2', 'sulfur_dioxide', 'so 2'],
            'CO': ['co', 'carbon_monoxide'],
            'O3': ['o3', 'ozone'],
            'AQI': ['aqi', 'air_quality_index'],
            'Time': ['time', 'date', 'datetime', 'timestamp'],
            'Temperature': ['temperature', 'temp'],
            'Humidity': ['humidity', 'hum'],
            'Pressure': ['pressure'],
            'WindSpeed': ['wind_speed', 'wind']
        }
    
    def clean_data(
        self,
        df: pd.DataFrame,
        missing_strategy: str = "median",
        outlier_method: str = "iqr",
        remove_duplicates: bool = True,
        constant_value: Any = 0,
        outlier_threshold: float = 1.5,
        zscore_threshold: float = 3.0
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        report = CleaningReport()
        report.original_rows = len(df)
        report.original_columns = len(df.columns)
        
        for col in df.columns:
            report.missing_values_before[col] = int(df[col].isna().sum())
        
        df_cleaned = df.copy()
        
        if remove_duplicates:
            rows_before = len(df_cleaned)
            df_cleaned = df_cleaned.drop_duplicates()
            report.duplicates_removed = rows_before - len(df_cleaned)
            if report.duplicates_removed > 0:
                report.add_step(
                    "移除重复行",
                    f"移除了 {report.duplicates_removed} 行重复数据",
                    rows_before,
                    len(df_cleaned)
                )
        
        df_cleaned = self._normalize_column_names(df_cleaned)
        
        rows_before = len(df_cleaned)
        df_cleaned, type_changes = self._convert_data_types(df_cleaned)
        report.data_type_changes = type_changes
        if type_changes:
            report.add_step(
                "数据类型转换",
                f"转换了 {len(type_changes)} 列的数据类型",
                rows_before,
                len(df_cleaned)
            )
        
        rows_before = len(df_cleaned)
        df_cleaned, missing_report = self._handle_missing_values(
            df_cleaned, missing_strategy, constant_value
        )
        for col in df_cleaned.columns:
            report.missing_values_after[col] = int(df_cleaned[col].isna().sum())
        if missing_report:
            report.add_step(
                "缺失值处理",
                f"使用策略: {missing_strategy}",
                rows_before,
                len(df_cleaned)
            )
        
        if outlier_method != self.OUTLIER_METHOD_NONE:
            rows_before = len(df_cleaned)
            df_cleaned, outliers_report = self._handle_outliers(
                df_cleaned, outlier_method, outlier_threshold, zscore_threshold
            )
            report.outliers_removed = outliers_report
            if sum(outliers_report.values()) > 0:
                report.add_step(
                    "异常值处理",
                    f"使用方法: {outlier_method}",
                    rows_before,
                    len(df_cleaned)
                )
        
        report.final_rows = len(df_cleaned)
        report.final_columns = len(df_cleaned.columns)
        
        return df_cleaned, report
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip().replace(' ', '_')
            
            for standard_name, variations in self.column_mappings.items():
                if col_lower in [v.lower() for v in variations]:
                    column_mapping[col] = standard_name
                    break
        
        return df.rename(columns=column_mapping)
    
    def _convert_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        df_cleaned = df.copy()
        type_changes = {}
        
        for col in df_cleaned.columns:
            col_lower = col.lower()
            original_dtype = str(df_cleaned[col].dtype)
            
            if any(time_key in col_lower for time_key in ['time', 'date', 'timestamp']):
                try:
                    df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    if str(df_cleaned[col].dtype) != original_dtype:
                        type_changes[col] = f"{original_dtype} -> datetime"
                except:
                    pass
            
            elif any(pollutant in col_lower for pollutant in ['pm', 'no2', 'so2', 'co', 'o3', 'aqi', 'temp', 'hum', 'pressure', 'wind']):
                try:
                    df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
                    if str(df_cleaned[col].dtype) != original_dtype:
                        type_changes[col] = f"{original_dtype} -> numeric"
                except:
                    pass
        
        return df_cleaned, type_changes
    
    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        strategy: str,
        constant_value: Any = 0
    ) -> Tuple[pd.DataFrame, Dict]:
        df_cleaned = df.copy()
        report = {}
        
        if strategy == self.MISSING_STRATEGY_DROP:
            df_cleaned = df_cleaned.dropna()
            return df_cleaned, {"method": "drop"}
        
        for col in df_cleaned.columns:
            if df_cleaned[col].isna().any():
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    if strategy == self.MISSING_STRATEGY_MEAN:
                        fill_value = df_cleaned[col].mean()
                        df_cleaned[col] = df_cleaned[col].fillna(fill_value)
                    elif strategy == self.MISSING_STRATEGY_MEDIAN:
                        fill_value = df_cleaned[col].median()
                        df_cleaned[col] = df_cleaned[col].fillna(fill_value)
                    elif strategy == self.MISSING_STRATEGY_MODE:
                        fill_value = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 0
                        df_cleaned[col] = df_cleaned[col].fillna(fill_value)
                    elif strategy == self.MISSING_STRATEGY_FFILL:
                        df_cleaned[col] = df_cleaned[col].ffill()
                        df_cleaned[col] = df_cleaned[col].fillna(0)
                    elif strategy == self.MISSING_STRATEGY_BFILL:
                        df_cleaned[col] = df_cleaned[col].bfill()
                        df_cleaned[col] = df_cleaned[col].fillna(0)
                    elif strategy == self.MISSING_STRATEGY_CONSTANT:
                        df_cleaned[col] = df_cleaned[col].fillna(constant_value)
                    report[col] = strategy
                elif pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
                    df_cleaned = df_cleaned.dropna(subset=[col])
                else:
                    df_cleaned[col] = df_cleaned[col].fillna('Unknown')
        
        return df_cleaned, report
    
    def _handle_outliers(
        self,
        df: pd.DataFrame,
        method: str,
        iqr_threshold: float = 1.5,
        zscore_threshold: float = 3.0
    ) -> Tuple[pd.DataFrame, Dict]:
        df_cleaned = df.copy()
        outliers_report = {}
        
        for col in df_cleaned.columns:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                col_lower = col.lower()
                
                if any(pollutant in col_lower for pollutant in ['pm', 'no2', 'so2', 'o3', 'aqi', 'temp', 'hum', 'pressure', 'wind', 'co']):
                    original_count = len(df_cleaned)
                    
                    if method == self.OUTLIER_METHOD_IQR:
                        Q1 = df_cleaned[col].quantile(0.25)
                        Q3 = df_cleaned[col].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        lower_bound = Q1 - iqr_threshold * IQR
                        upper_bound = Q3 + iqr_threshold * IQR
                        
                        median_value = df_cleaned[col].median()
                        df_cleaned[col] = df_cleaned[col].apply(
                            lambda x: median_value if (pd.notna(x) and (x < lower_bound or x > upper_bound)) else x
                        )
                    
                    elif method == self.OUTLIER_METHOD_ZSCORE:
                        mean = df_cleaned[col].mean()
                        std = df_cleaned[col].std()
                        
                        if std > 0:
                            z_scores = (df_cleaned[col] - mean) / std
                            median_value = df_cleaned[col].median()
                            df_cleaned[col] = df_cleaned[col].mask(
                                abs(z_scores) > zscore_threshold, median_value
                            )
                    
                    outliers_report[col] = original_count - len(df_cleaned[df_cleaned[col] == df_cleaned[col]])
        
        return df_cleaned, outliers_report
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "info": []
        }
        
        if len(df) == 0:
            validation["is_valid"] = False
            validation["issues"].append("数据集为空")
        
        if len(df.columns) < 2:
            validation["warnings"].append("数据集列数较少")
        
        time_columns = [col for col in df.columns 
                       if any(t in col.lower() for t in ['time', 'date', 'timestamp'])]
        if not time_columns:
            validation["warnings"].append("未检测到时间列")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            validation["issues"].append("没有数值列，无法进行分析")
            validation["is_valid"] = False
        
        for col in df.columns:
            missing_pct = df[col].isna().sum() / len(df) * 100
            if missing_pct > 50:
                validation["warnings"].append(f"列 '{col}' 缺失值超过 50% ({missing_pct:.1f}%)")
        
        validation["info"].append({
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": list(numeric_columns),
            "time_columns": time_columns
        })
        
        return validation

class AdvancedChartGenerator:
    CHART_LINE = "line"
    CHART_BAR = "bar"
    CHART_SCATTER = "scatter"
    CHART_AREA = "area"
    CHART_PIE = "pie"
    CHART_HEATMAP = "heatmap"
    
    def generate_chart_data(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_columns: List[str],
        title: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        if chart_type == self.CHART_LINE:
            return self._generate_line_chart(df, x_column, y_columns, title, **kwargs)
        elif chart_type == self.CHART_BAR:
            return self._generate_bar_chart(df, x_column, y_columns, title, **kwargs)
        elif chart_type == self.CHART_SCATTER:
            return self._generate_scatter_chart(df, x_column, y_columns, title, **kwargs)
        elif chart_type == self.CHART_AREA:
            return self._generate_area_chart(df, x_column, y_columns, title, **kwargs)
        elif chart_type == self.CHART_PIE:
            return self._generate_pie_chart(df, x_column, y_columns, title, **kwargs)
        elif chart_type == self.CHART_HEATMAP:
            return self._generate_heatmap(df, x_column, y_columns, title, **kwargs)
        else:
            return self._generate_line_chart(df, x_column, y_columns, title, **kwargs)
    
    def _generate_line_chart(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "趋势分析",
        smooth: bool = True,
        show_symbol: bool = True
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_LINE,
            "title": title,
            "x_axis": [],
            "series": [],
            "options": {
                "smooth": smooth,
                "show_symbol": show_symbol
            }
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
                    "type": self.CHART_LINE,
                    "smooth": smooth
                }
                result["series"].append(series_data)
        
        return result
    
    def _generate_bar_chart(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "对比分析",
        aggregate: str = "mean",
        horizontal: bool = False
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_BAR,
            "title": title,
            "x_axis": [],
            "series": [],
            "options": {
                "aggregate": aggregate,
                "horizontal": horizontal
            }
        }
        
        if x_column not in df.columns:
            return result
        
        if aggregate == "mean":
            grouped = df.groupby(x_column)[y_columns].mean()
        elif aggregate == "sum":
            grouped = df.groupby(x_column)[y_columns].sum()
        elif aggregate == "max":
            grouped = df.groupby(x_column)[y_columns].max()
        elif aggregate == "min":
            grouped = df.groupby(x_column)[y_columns].min()
        elif aggregate == "median":
            grouped = df.groupby(x_column)[y_columns].median()
        elif aggregate == "count":
            grouped = df.groupby(x_column)[y_columns].count()
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
                    "type": self.CHART_BAR
                }
                result["series"].append(series_data)
        
        return result
    
    def _generate_scatter_chart(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "散点图分析",
        symbol_size: int = 8
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_SCATTER,
            "title": title,
            "x_axis": [],
            "series": [],
            "options": {
                "symbol_size": symbol_size
            }
        }
        
        if x_column not in df.columns:
            return result
        
        x_data = df[x_column]
        if pd.api.types.is_numeric_dtype(x_data):
            result["x_axis_type"] = "value"
        elif pd.api.types.is_datetime64_any_dtype(x_data):
            result["x_axis_type"] = "time"
            result["x_axis"] = x_data.dt.strftime('%Y-%m-%d %H:%M').tolist()
        else:
            result["x_axis_type"] = "category"
            result["x_axis"] = x_data.astype(str).tolist()
        
        for y_col in y_columns:
            if y_col in df.columns and pd.api.types.is_numeric_dtype(df[y_col]):
                series_data = {
                    "name": y_col,
                    "data": list(zip(
                        x_data.tolist() if pd.api.types.is_numeric_dtype(x_data) else list(range(len(df))),
                        df[y_col].fillna(0).tolist()
                    )),
                    "type": self.CHART_SCATTER,
                    "symbolSize": symbol_size
                }
                result["series"].append(series_data)
        
        return result
    
    def _generate_area_chart(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "面积图分析",
        stack: bool = False
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_AREA,
            "title": title,
            "x_axis": [],
            "series": [],
            "options": {
                "stack": stack
            }
        }
        
        if x_column in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[x_column]):
                result["x_axis"] = df[x_column].dt.strftime('%Y-%m-%d %H:%M').tolist()
            else:
                result["x_axis"] = df[x_column].astype(str).tolist()
        
        for idx, y_col in enumerate(y_columns):
            if y_col in df.columns and pd.api.types.is_numeric_dtype(df[y_col]):
                series_data = {
                    "name": y_col,
                    "data": df[y_col].fillna(0).tolist(),
                    "type": self.CHART_LINE,
                    "areaStyle": {},
                    "smooth": True
                }
                if stack:
                    series_data["stack"] = "total"
                result["series"].append(series_data)
        
        return result
    
    def _generate_pie_chart(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "占比分析",
        radius: List[str] = ["0%", "70%"]
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_PIE,
            "title": title,
            "series": [],
            "options": {
                "radius": radius
            }
        }
        
        if len(y_columns) == 0:
            return result
        
        y_col = y_columns[0]
        if y_col not in df.columns:
            return result
        
        if x_column in df.columns:
            grouped = df.groupby(x_column)[y_col].sum()
            pie_data = [
                {"name": str(idx), "value": float(val) if pd.notna(val) else 0}
                for idx, val in grouped.items()
            ]
        else:
            total = df[y_col].sum()
            pie_data = [{"name": y_col, "value": float(total) if pd.notna(total) else 0}]
        
        result["series"] = [{
            "name": title,
            "type": self.CHART_PIE,
            "radius": radius,
            "data": pie_data,
            "label": {
                "show": True,
                "formatter": "{b}: {c} ({d}%)"
            }
        }]
        
        return result
    
    def _generate_heatmap(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "热力图分析"
    ) -> Dict[str, Any]:
        result = {
            "chart_type": self.CHART_HEATMAP,
            "title": title,
            "x_axis": [],
            "y_axis": y_columns,
            "data": [],
            "options": {}
        }
        
        if x_column not in df.columns:
            return result
        
        if pd.api.types.is_datetime64_any_dtype(df[x_column]):
            result["x_axis"] = df[x_column].dt.strftime('%Y-%m-%d %H:%M').tolist()
        else:
            result["x_axis"] = df[x_column].astype(str).tolist()
        
        heatmap_data = []
        for y_idx, y_col in enumerate(y_columns):
            if y_col in df.columns and pd.api.types.is_numeric_dtype(df[y_col]):
                for x_idx, val in enumerate(df[y_col]):
                    heatmap_data.append([x_idx, y_idx, float(val) if pd.notna(val) else 0])
        
        result["data"] = heatmap_data
        
        return result
    
    def generate_statistics_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        summary = {
            "total_records": len(df),
            "columns": list(df.columns),
            "numeric_columns": [],
            "time_columns": [],
            "categorical_columns": [],
            "statistics": {},
            "correlation": {}
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
                    "missing_count": int(df[col].isna().sum()),
                    "missing_percent": round(df[col].isna().sum() / len(df) * 100, 2)
                }
                summary["statistics"][col] = col_stats
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                summary["time_columns"].append(col)
            else:
                summary["categorical_columns"].append(col)
        
        if len(summary["numeric_columns"]) > 1:
            numeric_df = df[summary["numeric_columns"]]
            corr_matrix = numeric_df.corr()
            summary["correlation"] = corr_matrix.to_dict()
        
        return summary

data_cleaner = AdvancedDataCleaner()
chart_generator = AdvancedChartGenerator()
