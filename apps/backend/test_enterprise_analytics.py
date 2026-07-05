import os
import sys

# Append project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.analytics.analytics_engine import AnalyticsEngine
from app.services.analytics.insight_engine import AIInsightEngine


def verify_analytics_engine():
    print("=== STARTING ENTERPRISE ANALYTICS ENGINE VERIFICATION ===")

    # 1. Create a dummy sales CSV data for testing
    test_csv = "test_sales_data.csv"
    csv_content = """Month,Revenue,Expenses,OutlierCol
Jan,10000,5000,10
Feb,12000,5500,12
Mar,15000,6000,14
Apr,14000,5800,15
May,16000,6200,18
Jun,11000,5200,20
Jul,13000,5400,12
Aug,14500,5700,13
Sep,18000,7000,105
Oct,19000,7500,14
Nov,21000,8000,12
Dec,25000,9000,15"""

    with open(test_csv, "w", encoding="utf-8") as f:
        f.write(csv_content)

    print(f"Created sample dataset: {test_csv}")

    try:
        # 2. Test EDA Profiling & Descriptive Statistics
        print("\n1. Testing Exploratory Data Analysis & stats calculations...")
        profile = AnalyticsEngine._compute_profile(doc_id=999, file_path=test_csv)
        
        # Verify stats presence
        assert "descriptive_stats" in profile
        assert "Revenue" in profile["descriptive_stats"]
        
        revenue_stats = profile["descriptive_stats"]["Revenue"]
        print(f"Revenue Mean: {revenue_stats['mean']}")
        print(f"Revenue Median: {revenue_stats['median']}")
        print(f"Revenue Skewness: {revenue_stats['skewness']}")
        print(f"Revenue Kurtosis: {revenue_stats['kurtosis']}")
        
        assert "mean" in revenue_stats
        assert "median" in revenue_stats
        assert "mode" in revenue_stats
        assert "std_dev" in revenue_stats
        assert "variance" in revenue_stats
        assert "skewness" in revenue_stats
        assert "kurtosis" in revenue_stats
        assert "quartiles" in revenue_stats
        
        print("✅ Descriptive statistics assertions passed successfully!")

        # 3. Test Outlier Detection (IQR)
        print("\n2. Testing IQR-based Outlier Detection...")
        assert "outlier_reports" in profile
        outlier_col_rep = profile["outlier_reports"]["OutlierCol"]
        print(f"OutlierCol Outliers Count: {outlier_col_rep['count']}")
        print(f"OutlierCol Sample Outliers: {outlier_col_rep['sample_outliers']}")
        
        # Value 105 is way above Q3 + 1.5*IQR (IQR is small here)
        assert outlier_col_rep["count"] > 0
        assert 105.0 in outlier_col_rep["sample_outliers"]
        print("✅ IQR Outlier detection flagged correct outliers!")

        # 4. Test Pearson Correlation Matrix
        print("\n3. Testing Pearson Correlation Coefficients...")
        assert "correlation_matrix" in profile
        corr_val = profile["correlation_matrix"]["Revenue"]["Expenses"]
        print(f"Correlation (Revenue vs Expenses): {corr_val:.4f}")
        assert corr_val > 0.8  # Strong positive correlation as expenses grow with revenue in dummy data
        print("✅ Pearson correlation matrix computed strong positive correlation!")

        # 5. Test Quality Report and Imputation Recommendations
        print("\n4. Testing Quality warnings & Missing imputation recommenders...")
        assert "quality_report" in profile
        assert "imputation_recommendations" in profile
        print(f"Missing Cells Count: {profile['quality_report']['missing_cells']}")
        print("✅ Quality profile calculations completed successfully!")

        # 6. Test AI Chart Recommendations
        print("\n5. Testing Automatic Chart Recommendations...")
        assert "chart_recommendations" in profile
        print(f"Total Chart Recommendations: {len(profile['chart_recommendations'])}")
        for rec in profile["chart_recommendations"]:
            print(f"- Recommended: {rec['chart_type']} | Reason: {rec['reason']}")
        print("✅ Chart recommendations extracted successfully!")

        # 7. Test Caching Serialization
        print("\n6. Testing caching system storage and retrieval...")
        cached_profile = AnalyticsEngine.get_profile(doc_id=999, file_path=test_csv)
        assert "rows_count" in cached_profile
        
        # Test loading from cache
        loaded_profile = AnalyticsEngine.get_profile(doc_id=999, file_path=test_csv)
        assert loaded_profile["rows_count"] == cached_profile["rows_count"]
        print("✅ Serialization caching system is working and robust!")

    finally:
        # Clean up test file
        if os.path.exists(test_csv):
            os.remove(test_csv)
        
        # Clean up cache file
        cache_file = os.path.join("storage", "analytics_cache", "doc_999.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)

    print("\n🎉 ALL ENTERPRISE ANALYTICS ENGINE TESTS COMPLETED AND VERIFIED!")


if __name__ == "__main__":
    verify_analytics_engine()
