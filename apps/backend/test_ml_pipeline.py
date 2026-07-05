import os
import sys

# Append project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ml.ml_service import MLService


def verify_ml_pipeline():
    print("=== STARTING MACHINE LEARNING STUDIO VERIFICATION ===")

    # 1. Create a dummy classification CSV for testing
    test_csv = "test_churn_data.csv"
    csv_content = """Age,Income,Churn,Tenure
25,30000,Yes,3
35,60000,No,12
45,80000,No,24
20,22000,Yes,1
55,95000,No,48
60,110000,No,60
28,35000,Yes,2
40,70000,No,18
22,25000,Yes,1
38,62000,No,10"""

    with open(test_csv, "w", encoding="utf-8") as f:
        f.write(csv_content)

    print(f"Created sample dataset: {test_csv}")

    try:
        # 2. Test columns scanning & target recommendations
        print("\n1. Testing columns scanning & target recommendations...")
        options = MLService.get_features_and_targets(test_csv)
        assert "columns" in options
        assert options["total_rows"] == 10
        
        churn_col = next(c for c in options["columns"] if c["name"] == "Churn")
        print(f"Churn Column Type: {churn_col['type']}")
        print(f"Churn Recommended Target: {churn_col['recommended_target']}")
        assert churn_col["recommended_target"] is True
        print("✅ Column options scanning passed successfully!")

        # 3. Test Pipeline Training (Classification)
        print("\n2. Testing model pipeline training (Classification)...")
        train_res = MLService.train_pipeline(
            doc_id=777,
            file_path=test_csv,
            target_col="Churn",
            feature_cols=["Age", "Income", "Tenure"],
            algorithm="random_forest"
        )
        
        assert train_res["success"] is True
        assert train_res["task_type"] == "classification"
        assert "accuracy" in train_res["metrics"]
        print(f"Train Accuracy: {train_res['metrics']['accuracy']}")
        print(f"Feature Importance List: {train_res['feature_importance']}")
        
        # Verify feature importance contains keys we trained
        features_trained = [fi["feature"] for fi in train_res["feature_importance"]]
        assert "Age" in features_trained
        assert "Income" in features_trained
        print("✅ Pipeline training completed successfully!")

        # 4. Test Inference Prediction
        print("\n3. Testing prediction inference...")
        inputs = {"Age": 24, "Income": 28000, "Tenure": 2}
        pred_res = MLService.make_prediction(doc_id=777, inputs=inputs)
        
        assert "prediction" in pred_res
        assert pred_res["task_type"] == "classification"
        print(f"Prediction: {pred_res['prediction']}")
        print(f"Confidence: {pred_res['confidence']}")
        print("✅ Live prediction inference completed successfully!")

    finally:
        # Clean up test file
        if os.path.exists(test_csv):
            os.remove(test_csv)
        
        # Clean up joblib model file
        joblib_file = os.path.join("storage", "ml_models", "model_777.joblib")
        if os.path.exists(joblib_file):
            os.remove(joblib_file)

    print("\n🎉 ALL MACHINE LEARNING PIPELINE TESTS COMPLETED AND VERIFIED!")


if __name__ == "__main__":
    verify_ml_pipeline()
