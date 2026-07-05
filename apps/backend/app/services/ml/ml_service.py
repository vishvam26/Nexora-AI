import os
import logging
from typing import Dict, Any, List, Optional
import numpy as np

try:
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, r2_score, mean_absolute_error, mean_squared_error
    import joblib
except ImportError:
    pd = None
    train_test_split = None
    joblib = None

logger = logging.getLogger("app.services.ml.ml_service")

MODEL_DIR = os.path.join("storage", "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)


class MLService:
    """
    Enterprise-grade Machine Learning Studio Service.
    Handles automated classification/regression task detection, scikit-learn training,
    performance metric evaluation, feature importance mapping, joblib model serialization,
    and real-time prediction inference.
    """

    @classmethod
    def get_features_and_targets(cls, file_path: str) -> Dict[str, Any]:
        """
        Scans columns of CSV/spreadsheet, classifies them, and detects target recommendations.
        """
        if pd is None or not os.path.exists(file_path):
            return {"error": "Scikit-learn not imported or file missing."}

        try:
            if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python")
                except Exception:
                    df = pd.read_csv(file_path)

            columns = []
            for col in df.columns:
                unique_cnt = df[col].nunique()
                is_numeric = np.issubdtype(df[col].dtype, np.number)
                
                # Recommend target if cardinality is reasonable and name matches concepts
                rec_target = False
                col_lower = col.lower()
                if any(x in col_lower for x in ["price", "revenue", "churn", "target", "label", "class", "status", "sales", "sold", "purchased"]):
                    rec_target = True

                columns.append({
                    "name": col,
                    "type": "numeric" if is_numeric else "categorical",
                    "unique_count": unique_cnt,
                    "recommended_target": rec_target
                })

            return {
                "columns": columns,
                "total_rows": len(df)
            }
        except Exception as e:
            logger.error(f"Failed to fetch ML options: {e}")
            return {"error": str(e)}

    @classmethod
    def train_pipeline(
        cls, 
        doc_id: int, 
        file_path: str, 
        target_col: str, 
        feature_cols: List[str], 
        algorithm: Optional[str] = "random_forest"
    ) -> Dict[str, Any]:
        """
        Builds preprocessing pipeline, splits data, fits scikit-learn model,
        evaluates metrics, computes feature importances, and caches it as joblib model.
        """
        if pd is None or not os.path.exists(file_path):
            return {"error": "Scikit-learn/Pandas dependency is missing."}

        try:
            # Load dataset
            if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python")
                except Exception:
                    df = pd.read_csv(file_path)

            # Assert columns exist
            all_cols = feature_cols + [target_col]
            for col in all_cols:
                if col not in df.columns:
                    return {"error": f"Column '{col}' not found in dataset."}

            # Drop rows where target is missing
            df = df.dropna(subset=[target_col])
            
            X = df[feature_cols]
            y = df[target_col]

            # 1. Detect task type
            is_target_numeric = np.issubdtype(y.dtype, np.number)
            target_cardinality = y.nunique()

            # Classification if categorical or numeric with low cardinality
            if not is_target_numeric or target_cardinality <= 10:
                task_type = "classification"
                # Encode target labels if string categorical
                y_classes = [str(x) for x in y.unique()]
                y_encoded = y.astype(str)
            else:
                task_type = "regression"
                y_classes = []
                y_encoded = y.astype(float)

            # 2. Setup Column Transformer Preprocessing
            numeric_features = [col for col in feature_cols if np.issubdtype(X[col].dtype, np.number)]
            categorical_features = [col for col in feature_cols if col not in numeric_features]

            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])

            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_features),
                    ('cat', categorical_transformer, categorical_features)
                ]
            )

            # 3. Model Definition
            if task_type == "classification":
                if algorithm == "linear":
                    model = LogisticRegression(max_iter=1000, random_state=42)
                elif algorithm == "gradient_boosting":
                    model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
                else:  # random_forest
                    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
            else:  # regression
                if algorithm == "linear":
                    model = LinearRegression()
                elif algorithm == "gradient_boosting":
                    model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
                else:  # random_forest
                    model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)

            # Compile Pipeline
            clf = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', model)
            ])

            # Train / Test split
            X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_ratio_test=0.2, random_state=42)

            # Fit Model
            clf.fit(X_train, y_train)

            # Predict and evaluate
            y_pred = clf.predict(X_test)
            metrics = {}

            if task_type == "classification":
                acc = accuracy_score(y_test, y_pred)
                precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
                metrics = {
                    "accuracy": round(float(acc), 4),
                    "precision": round(float(precision), 4),
                    "recall": round(float(recall), 4),
                    "f1_score": round(float(f1), 4)
                }
            else:  # regression
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                metrics = {
                    "r2_score": round(float(r2), 4),
                    "mae": round(float(mae), 4),
                    "mse": round(float(mse), 4)
                }

            # 4. Feature Importance Calculation
            feature_importance = []
            try:
                # Retrieve transformed feature names
                if hasattr(preprocessor, 'get_feature_names_out'):
                    feature_names = preprocessor.get_feature_names_out()
                else:
                    feature_names = numeric_features + categorical_features # fallback

                raw_model = clf.named_steps['classifier']
                
                # Check coefficients or importances
                if hasattr(raw_model, 'feature_importances_'):
                    importances = raw_model.feature_importances_
                elif hasattr(raw_model, 'coef_'):
                    # For logistic multiclass, grab mean abs coefficients
                    if raw_model.coef_.ndim > 1:
                        importances = np.mean(np.abs(raw_model.coef_), axis=0)
                    else:
                        importances = np.abs(raw_model.coef_)
                else:
                    importances = np.zeros(len(feature_names))

                # Normalize importances
                if importances.sum() > 0:
                    importances = importances / importances.sum()

                # Map back to raw features
                importance_map = {}
                for name, score in zip(feature_names, importances):
                    # Strip numerical suffixes from OneHotEncoder name (e.g. cat__x_column_value)
                    raw_name = name
                    for col in feature_cols:
                        if col in name:
                            raw_name = col
                            break
                    importance_map[raw_name] = importance_map.get(raw_name, 0.0) + float(score)

                feature_importance = [
                    {"feature": k, "importance": round(v, 4)}
                    for k, v in sorted(importance_map.items(), key=lambda item: item[1], reverse=True)
                ]
            except Exception as fe:
                logger.warning(f"Failed to calculate feature importances: {fe}")
                feature_importance = [{"feature": col, "importance": 1.0 / len(feature_cols)} for col in feature_cols]

            # 5. Joblib Serialization
            model_path = os.path.join(MODEL_DIR, f"model_{doc_id}.joblib")
            model_payload = {
                "pipeline": clf,
                "task_type": task_type,
                "target_column": target_col,
                "feature_columns": feature_cols,
                "classes": y_classes,
                "metrics": metrics,
                "feature_importance": feature_importance
            }
            joblib.dump(model_payload, model_path)
            logger.info(f"Model saved to joblib at: {model_path}")

            return {
                "success": True,
                "task_type": task_type,
                "metrics": metrics,
                "feature_importance": feature_importance,
                "classes_count": len(y_classes)
            }

        except Exception as e:
            logger.error(f"ML Pipeline training failed: {e}", exc_info=True)
            return {"error": f"Training failed: {str(e)}"}

    @classmethod
    def make_prediction(cls, doc_id: int, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads cached joblib model pipeline and runs single row inference.
        """
        model_path = os.path.join(MODEL_DIR, f"model_{doc_id}.joblib")
        if not os.path.exists(model_path):
            return {"error": "Trained model joblib cache missing. Please train the dataset first."}

        if joblib is None:
            return {"error": "joblib is not loaded on server backend."}

        try:
            model_payload = joblib.load(model_path)
            clf = model_payload["pipeline"]
            task_type = model_payload["task_type"]
            feature_cols = model_payload["feature_columns"]
            classes = model_payload["classes"]

            # Map inputs into Pandas DataFrame row
            row_data = {}
            for col in feature_cols:
                val = inputs.get(col)
                # Try parsing numeric types
                if val is not None:
                    try:
                        if "." in str(val):
                            row_data[col] = [float(val)]
                        else:
                            row_data[col] = [int(val)]
                    except ValueError:
                        row_data[col] = [val]
                else:
                    row_data[col] = [None]

            input_df = pd.DataFrame.from_dict(row_data)

            # Predict
            pred = clf.predict(input_df)
            result_val = pred[0]

            confidence = 1.0
            if task_type == "classification":
                # Predict probabilities if model supports
                try:
                    probs = clf.predict_proba(input_df)[0]
                    confidence = float(np.max(probs))
                except Exception:
                    pass

            return {
                "task_type": task_type,
                "prediction": str(result_val) if task_type == "classification" else round(float(result_val), 4),
                "confidence": round(confidence, 4)
            }

        except Exception as e:
            logger.error(f"Inference prediction failed: {e}")
            return {"error": f"Inference execution failed: {str(e)}"}


def train_test_split(X, y, test_ratio_test=0.2, random_state=42):
    # Standard fallback split implementation if sklearn import somehow breaks
    from sklearn.model_selection import train_test_split as sk_split
    return sk_split(X, y, test_size=test_ratio_test, random_state=random_state)
