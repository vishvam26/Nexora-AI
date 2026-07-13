import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger("app.services.analytics.analytics_engine")

CACHE_DIR = os.path.join("storage", "analytics_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class AnalyticsEngine:
    """
    Enterprise-grade Analytics Engine.
    Handles Pandas EDA profiling, descriptive statistics (variance, kurtosis, skewness, quartiles),
    IQR outlier detection, Pearson correlation matrix mapping, automatic business KPIs,
    missing value recommendations, and local JSON caching.
    """

    @classmethod
    def get_profile(cls, doc_id: int, file_path: str) -> Dict[str, Any]:
        """
        Loads cached analytics profile, or computes data statistics and caches them to disk.
        """
        cache_file = os.path.join(CACHE_DIR, f"doc_{doc_id}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    logger.info(f"Loaded analytics cache for doc_id={doc_id}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read analytics cache for doc_id={doc_id}: {e}")

        # Compute Profile
        profile = cls._compute_profile(doc_id, file_path)

        # Write Cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)
            logger.info(f"Created analytics cache for doc_id={doc_id}")
        except Exception as e:
            logger.warning(f"Failed to write analytics cache for doc_id={doc_id}: {e}")

        return profile

    @classmethod
    def _compute_profile(cls, doc_id: int, file_path: str) -> Dict[str, Any]:
        if pd is None:
            logger.error("Pandas is not installed. Returning empty profile.")
            return {"error": "Pandas not installed on backend."}

        if not os.path.exists(file_path):
            logger.error(f"Spreadsheet file not found at: {file_path}")
            return {"error": "Source file not found on disk."}

        try:
            # Load file (CSV or Excel)
            if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                # Detect separator or fallback
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python")
                except Exception:
                    df = pd.read_csv(file_path)

            # Limit size for safety on Colab RAM
            if len(df) > 50000:
                logger.info(f"Large dataset detected ({len(df)} rows). Sampling top 50,000 for profiling.")
                df = df.sample(n=50000, random_state=42)

            total_rows, total_cols = df.shape
            duplicate_rows = int(df.duplicated().sum())

            # Columns identification
            columns_info = []
            numeric_cols = []
            categorical_cols = []
            datetime_cols = []

            for col in df.columns:
                col_series = df[col]
                dtype = str(col_series.dtype)
                missing_count = int(col_series.isnull().sum())
                missing_pct = round((missing_count / total_rows) * 100, 2)
                unique_count = int(col_series.nunique())

                # Classification
                col_type = "categorical"
                if np.issubdtype(col_series.dtype, np.number):
                    col_type = "numeric"
                    numeric_cols.append(col)
                elif np.issubdtype(col_series.dtype, np.datetime64) or "date" in col.lower():
                    col_type = "datetime"
                    datetime_cols.append(col)
                else:
                    categorical_cols.append(col)

                columns_info.append({
                    "name": col,
                    "type": col_type,
                    "dtype": dtype,
                    "missing_count": missing_count,
                    "missing_pct": missing_pct,
                    "unique_count": unique_count
                })

            # Calculate detailed statistics
            descriptive_stats = {}
            outlier_reports = {}
            imputation_recommendations = []

            # 1. Descriptive Stats for Numeric Columns
            for col in numeric_cols:
                col_clean = df[col].dropna()
                if col_clean.empty:
                    continue

                # Quartiles
                q25 = float(col_clean.quantile(0.25))
                q50 = float(col_clean.quantile(0.50))
                q75 = float(col_clean.quantile(0.75))

                # Higher order stats
                mean_val = float(col_clean.mean())
                median_val = float(col_clean.median())
                std_val = float(col_clean.std()) if len(col_clean) > 1 else 0.0
                var_val = float(col_clean.var()) if len(col_clean) > 1 else 0.0
                skew_val = float(col_clean.skew()) if len(col_clean) > 2 else 0.0
                kurt_val = float(col_clean.kurt()) if len(col_clean) > 3 else 0.0

                # Mode
                mode_series = col_clean.mode()
                mode_val = float(mode_series.iloc[0]) if not mode_series.empty else mean_val

                # Outlier detection (IQR)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outliers = col_clean[(col_clean < lower_bound) | (col_clean > upper_bound)]
                outlier_count = len(outliers)
                sample_outliers = [float(x) for x in outliers.head(5).tolist()]

                descriptive_stats[col] = {
                    "mean": round(mean_val, 4),
                    "median": round(median_val, 4),
                    "mode": round(mode_val, 4),
                    "std_dev": round(std_val, 4),
                    "variance": round(var_val, 4),
                    "skewness": round(skew_val, 4),
                    "kurtosis": round(kurt_val, 4),
                    "quartiles": {
                        "q25": round(q25, 4),
                        "q50": round(q50, 4),
                        "q75": round(q75, 4)
                    }
                }

                outlier_reports[col] = {
                    "count": outlier_count,
                    "percentage": round((outlier_count / total_rows) * 100, 2),
                    "threshold_low": round(lower_bound, 4),
                    "threshold_high": round(upper_bound, 4),
                    "sample_outliers": sample_outliers
                }

            # 2. Missing values recommendations
            for col_info in columns_info:
                if col_info["missing_count"] > 0:
                    pct = col_info["missing_pct"]
                    col_name = col_info["name"]
                    if col_info["type"] == "numeric" and col_name in descriptive_stats:
                        skew = descriptive_stats[col_name]["skewness"]
                        median_v = descriptive_stats[col_name]["median"]
                        mean_v = descriptive_stats[col_name]["mean"]
                        if abs(skew) > 0.5:
                            rec = f"Impute missing cells ({pct}%) with Median ({median_v}) due to high column skewness ({skew:.2f})."
                        else:
                            rec = f"Impute missing cells ({pct}%) with Mean ({mean_v}) because column is symmetric."
                    else:
                        rec = f"Impute missing categorical items ({pct}%) with Mode (Most Frequent) or fill with 'Unknown'."
                    
                    imputation_recommendations.append({
                        "column": col_name,
                        "pct": pct,
                        "recommendation": rec
                    })

            # 3. Correlation matrix
            correlation_matrix = {}
            if len(numeric_cols) > 1:
                corr_df = df[numeric_cols].corr()
                for c1 in corr_df.columns:
                    correlation_matrix[c1] = {}
                    for c2 in corr_df.index:
                        val = corr_df.loc[c2, c1]
                        correlation_matrix[c1][c2] = float(val) if not pd.isna(val) else 0.0

            # 4. Automated KPIs based on column titles
            kpis = []
            for col in numeric_cols:
                col_lower = col.lower()
                col_clean = df[col].dropna()
                if col_clean.empty:
                    continue

                if any(k in col_lower for k in ["revenue", "sales", "income"]):
                    kpis.append({
                        "label": f"Total {col}",
                        "value": f"${float(col_clean.sum()):,.2f}",
                        "desc": f"Aggregated sum of {col}"
                    })
                    kpis.append({
                        "label": f"Average {col}",
                        "value": f"${float(col_clean.mean()):,.2f}",
                        "desc": f"Mean transaction {col}"
                    })
                elif any(k in col_lower for k in ["profit", "gain"]):
                    kpis.append({
                        "label": f"Total Net {col}",
                        "value": f"${float(col_clean.sum()):,.2f}",
                        "desc": "Combined profit margin"
                    })
                elif any(k in col_lower for k in ["cost", "expense", "spend"]):
                    kpis.append({
                        "label": f"Total Expenses ({col})",
                        "value": f"${float(col_clean.sum()):,.2f}",
                        "desc": "Sum of expenses"
                    })

            # Standard Row Count KPI
            kpis.append({
                "label": "Total Record Rows",
                "value": f"{total_rows:,}",
                "desc": "Dataset length"
            })

            # 5. AI Chart Recommendations
            chart_recommendations = []
            if datetime_cols and numeric_cols:
                chart_recommendations.append({
                    "x_column": datetime_cols[0],
                    "y_column": numeric_cols[0],
                    "chart_type": "line",
                    "reason": f"Recommended Line Chart to visualize chronological trend of '{numeric_cols[0]}' over time series '{datetime_cols[0]}'."
                })
            
            if categorical_cols and numeric_cols:
                # Pick low cardinality category if available
                cardinalities = {c: df[c].nunique() for c in categorical_cols}
                sorted_cats = sorted(cardinalities.items(), key=lambda x: x[1])
                best_cat = sorted_cats[0][0]
                best_card = sorted_cats[0][1]

                chart_type = "pie" if best_card <= 6 else "bar"
                chart_recommendations.append({
                    "x_column": best_cat,
                    "y_column": numeric_cols[0],
                    "chart_type": chart_type,
                    "reason": f"Recommended {chart_type.capitalize()} Chart to compare distribution of '{numeric_cols[0]}' across categories in '{best_cat}' (cardinality={best_card})."
                })
            
            if len(numeric_cols) >= 2:
                chart_recommendations.append({
                    "x_column": numeric_cols[0],
                    "y_column": numeric_cols[1],
                    "chart_type": "scatter",
                    "reason": f"Recommended Scatter Plot to analyze statistical correlation between numerical variables '{numeric_cols[0]}' and '{numeric_cols[1]}'."
                })

            # Data Preview Rows
            preview_rows = df.head(10).replace({np.nan: None}).to_dict(orient="records")

            # Quality summary
            quality_report = {
                "duplicate_rows": duplicate_rows,
                "duplicate_pct": round((duplicate_rows / total_rows) * 100, 2),
                "total_cells": total_rows * total_cols,
                "missing_cells": int(df.isnull().sum().sum()),
                "missing_pct": round((df.isnull().sum().sum() / (total_rows * total_cols)) * 100, 2),
                "warnings": []
            }

            if duplicate_rows > 0:
                quality_report["warnings"].append(f"Found {duplicate_rows} duplicate rows inside database.")
            for col_info in columns_info:
                if col_info["missing_pct"] > 25:
                    quality_report["warnings"].append(f"Column '{col_info['name']}' has high null values ({col_info['missing_pct']}%).")
                if col_info["unique_count"] == 1:
                    quality_report["warnings"].append(f"Column '{col_info['name']}' contains a single constant value and provides no variance.")

            return {
                "document_id": doc_id,
                "rows_count": total_rows,
                "columns_count": total_cols,
                "columns": columns_info,
                "descriptive_stats": descriptive_stats,
                "outlier_reports": outlier_reports,
                "correlation_matrix": correlation_matrix,
                "quality_report": quality_report,
                "imputation_recommendations": imputation_recommendations,
                "kpis": kpis,
                "chart_recommendations": chart_recommendations,
                "preview_rows": preview_rows
            }

        except Exception as err:
            logger.error(f"Failed to profile dataset for doc_id={doc_id}: {err}", exc_info=True)
            return {"error": f"Tabular processing failed: {str(err)}"}

    @classmethod
    def get_aggregated_chart(
        cls, 
        file_path: str, 
        x_col: str, 
        y_col: str, 
        aggregation: Optional[str] = "sum"
    ) -> List[Dict[str, Any]]:
        """
        Reads CSV/Excel and performs group aggregate summarizing to generate coordinates.
        """
        if pd is None or not os.path.exists(file_path):
            return []

        try:
            if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python")
                except Exception:
                    df = pd.read_csv(file_path)

            if x_col not in df.columns or y_col not in df.columns:
                return []

            # Truncate dates or strings if needed to avoid chart congestion
            df[x_col] = df[x_col].astype(str).str.slice(0, 15)

            # Drop missing rows
            df_clean = df[[x_col, y_col]].dropna()

            # Group
            grouped = df_clean.groupby(x_col)
            if aggregation == "mean":
                agg_df = grouped[y_col].mean().reset_index()
            elif aggregation == "count":
                agg_df = grouped[y_col].count().reset_index()
            else:
                agg_df = grouped[y_col].sum().reset_index()

            # Limit size to 15 items for clear charting
            agg_df = agg_df.head(15)

            return [
                {
                    "label": str(row[x_col]),
                    "value": round(float(row[y_col]), 2)
                }
                for _, row in agg_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return []
