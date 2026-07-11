import os
import json
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
REGISTRY_DIR = os.path.join("storage", "ml_registry")
SHAP_DIR = os.path.join("storage", "ml_shap")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REGISTRY_DIR, exist_ok=True)
os.makedirs(SHAP_DIR, exist_ok=True)


class MLService:
    """
    Enterprise-grade Machine Learning Studio Service.
    Handles automated classification/regression task detection, scikit-learn training,
    performance metric evaluation, feature importance mapping, joblib model serialization,
    and real-time prediction inference.

    Architecture Hooks (Step 10 ready):
    - SHAP Explainability: shap_explain() computes per-sample feature attributions.
    - Model Registry: register_run() stores multi-algorithm run history per document.
    - Model Comparison: get_comparison() returns all runs sorted by primary metric.
    - ML Session: get_session_metadata() exposes a structured dict consumable by AI Agents.
    """

    @classmethod
    def get_features_and_targets(cls, file_path: str) -> Dict[str, Any]:
        """
        Scans columns of CSV/spreadsheet, classifies them, and detects target recommendations.
        """
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join("uploads", "knowledge", file_path))

        if pd is None or not os.path.exists(file_path):
            return {"error": f"Scikit-learn not imported or file missing. Checked: {file_path}"}

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
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join("uploads", "knowledge", file_path))

        if pd is None or not os.path.exists(file_path):
            return {"error": f"Scikit-learn/Pandas dependency is missing or file not found. Checked: {file_path}"}

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

            # 5. Joblib Serialization — keyed by algorithm to support Model Registry
            model_key = f"{doc_id}_{algorithm}"
            model_path = os.path.join(MODEL_DIR, f"model_{model_key}.joblib")
            # Also write the "active" model (latest train always overwrites active slot)
            active_model_path = os.path.join(MODEL_DIR, f"model_{doc_id}.joblib")

            model_payload = {
                "pipeline": clf,
                "task_type": task_type,
                "algorithm": algorithm,
                "target_column": target_col,
                "feature_columns": feature_cols,
                "numeric_features": numeric_features,
                "categorical_features": categorical_features,
                "classes": y_classes,
                "metrics": metrics,
                "feature_importance": feature_importance,
                # Store X_test sample for SHAP hook (max 200 rows to cap memory)
                "X_test_sample": X_test.head(200).to_dict(orient="list")
            }
            joblib.dump(model_payload, model_path)
            joblib.dump(model_payload, active_model_path)
            logger.info(f"Model saved: {model_path} | Active: {active_model_path}")

            # 6. Register run in Model Registry (multi-algorithm comparison hook)
            cls._register_run(doc_id, algorithm, task_type, metrics, feature_importance)

            result = {
                "success": True,
                "task_type": task_type,
                "algorithm": algorithm,
                "metrics": metrics,
                "feature_importance": feature_importance,
                "classes_count": len(y_classes)
            }

            # 7. SHAP Hook — compute and cache attributions immediately post-training
            #    (graceful no-op if shap library absent; AI Agents check shap_available flag)
            shap_result = cls._compute_shap(model_payload, doc_id)
            result["shap_available"] = shap_result.get("available", False)
            result["shap_summary"] = shap_result.get("summary", [])

            return result

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


    # ─────────────────────────────────────────────────────────────────
    # Architecture Hook 1: SHAP Explainability
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _compute_shap(cls, model_payload: Dict[str, Any], doc_id: int) -> Dict[str, Any]:
        """
        SHAP Explainability Hook.
        Attempts TreeExplainer for tree-based models, falls back to LinearExplainer.
        Stores feature-level mean |SHAP| values in storage/ml_shap/shap_{doc_id}.json.
        Returns a lightweight summary dict — full SHAP arrays stay on disk.

        Step 10 AI Agents can call: GET /ml/explain/{doc_id} to retrieve this.
        """
        shap_path = os.path.join(SHAP_DIR, f"shap_{doc_id}.json")
        try:
            import shap  # optional dependency — soft import
        except ImportError:
            logger.info("SHAP library not installed — skipping explainability compute. "
                        "Install with: pip install shap")
            return {"available": False, "reason": "shap library not installed"}

        try:
            clf = model_payload["pipeline"]
            feature_cols = model_payload["feature_columns"]
            X_test_dict = model_payload.get("X_test_sample", {})
            if not X_test_dict:
                return {"available": False, "reason": "No X_test sample stored in model payload"}

            X_test_df = pd.DataFrame.from_dict(X_test_dict)

            # Transform through preprocessor step
            preprocessor = clf.named_steps["preprocessor"]
            raw_model = clf.named_steps["classifier"]
            X_transformed = preprocessor.transform(X_test_df)

            # Choose explainer by model type
            tree_models = (RandomForestClassifier, RandomForestRegressor,
                           GradientBoostingClassifier, GradientBoostingRegressor)

            if isinstance(raw_model, tree_models):
                explainer = shap.TreeExplainer(raw_model)
                shap_values = explainer.shap_values(X_transformed)
            else:
                background = shap.kmeans(X_transformed, min(50, X_transformed.shape[0]))
                explainer = shap.KernelExplainer(raw_model.predict, background)
                shap_values = explainer.shap_values(X_transformed[:50], nsamples=100)

            # Resolve feature names from preprocessor
            if hasattr(preprocessor, "get_feature_names_out"):
                transformed_names = list(preprocessor.get_feature_names_out())
            else:
                transformed_names = [f"f_{i}" for i in range(X_transformed.shape[1])]

            # Collapse multiclass shap (take mean over classes)
            if isinstance(shap_values, list):
                shap_arr = np.mean([np.abs(sv) for sv in shap_values], axis=0)
            else:
                shap_arr = np.abs(shap_values)

            mean_abs_shap = np.mean(shap_arr, axis=0)

            # Map back to raw feature names
            shap_map: Dict[str, float] = {}
            for fname, val in zip(transformed_names, mean_abs_shap):
                raw_name = fname
                for col in feature_cols:
                    if col in fname:
                        raw_name = col
                        break
                shap_map[raw_name] = shap_map.get(raw_name, 0.0) + float(val)

            summary = [
                {"feature": k, "mean_abs_shap": round(v, 6)}
                for k, v in sorted(shap_map.items(), key=lambda x: x[1], reverse=True)
            ]

            # Persist to disk
            shap_cache = {
                "doc_id": doc_id,
                "algorithm": model_payload.get("algorithm"),
                "task_type": model_payload.get("task_type"),
                "summary": summary
            }
            with open(shap_path, "w", encoding="utf-8") as f:
                json.dump(shap_cache, f, indent=2)

            logger.info(f"SHAP values cached at {shap_path}")
            return {"available": True, "summary": summary}

        except Exception as e:
            logger.warning(f"SHAP computation failed (non-fatal): {e}")
            return {"available": False, "reason": str(e)}

    @classmethod
    def get_shap_explanation(cls, doc_id: int) -> Dict[str, Any]:
        """
        Public SHAP retrieval hook.
        Returns cached SHAP summary for the given document.
        If SHAP was never computed or library absent, returns status dict.
        Step 10 AI Agents call this to explain model predictions in reports.
        """
        shap_path = os.path.join(SHAP_DIR, f"shap_{doc_id}.json")
        if not os.path.exists(shap_path):
            return {"available": False, "reason": "SHAP cache not found. Run training first."}
        try:
            with open(shap_path, "r", encoding="utf-8") as f:
                return {"available": True, **json.load(f)}
        except Exception as e:
            return {"available": False, "reason": str(e)}

    # ─────────────────────────────────────────────────────────────────
    # Architecture Hook 2: Model Registry & Comparison
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def _register_run(cls, doc_id: int, algorithm: str, task_type: str,
                      metrics: Dict[str, float], feature_importance: List[Dict]) -> None:
        """
        Model Registry Hook.
        Appends each training run (algorithm + metrics) to a per-document JSON registry.
        This allows Model Comparison without re-training.
        Stored at: storage/ml_registry/registry_{doc_id}.json
        """
        import time
        registry_path = os.path.join(REGISTRY_DIR, f"registry_{doc_id}.json")

        # Load existing registry
        runs: List[Dict[str, Any]] = []
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    runs = json.load(f)
            except Exception:
                runs = []

        # Compute primary metric for sorting
        if task_type == "classification":
            primary_metric = "accuracy"
            primary_value = metrics.get("accuracy", 0.0)
        else:
            primary_metric = "r2_score"
            primary_value = metrics.get("r2_score", 0.0)

        run_entry = {
            "algorithm": algorithm,
            "task_type": task_type,
            "primary_metric": primary_metric,
            "primary_value": primary_value,
            "metrics": metrics,
            "top_features": feature_importance[:3],  # top-3 for quick comparison
            "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Remove previous run for same algorithm (avoid duplicates)
        runs = [r for r in runs if r.get("algorithm") != algorithm]
        runs.append(run_entry)

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(runs, f, indent=2)

        logger.info(f"Registered run [{algorithm}] in registry for doc_id={doc_id}")

    @classmethod
    def get_model_comparison(cls, doc_id: int) -> Dict[str, Any]:
        """
        Model Comparison Hook.
        Returns all algorithm runs for a document, sorted by primary metric desc.
        Step 10 AI Agents call this to select the best model for report generation.
        """
        registry_path = os.path.join(REGISTRY_DIR, f"registry_{doc_id}.json")
        if not os.path.exists(registry_path):
            return {"runs": [], "best_algorithm": None, "message": "No training runs registered yet."}

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                runs = json.load(f)

            # Sort best first
            runs_sorted = sorted(runs, key=lambda r: r.get("primary_value", 0.0), reverse=True)
            best = runs_sorted[0]["algorithm"] if runs_sorted else None

            return {
                "doc_id": doc_id,
                "runs": runs_sorted,
                "best_algorithm": best,
                "total_runs": len(runs_sorted)
            }
        except Exception as e:
            logger.error(f"Model comparison fetch failed: {e}")
            return {"runs": [], "best_algorithm": None, "message": str(e)}

    # ─────────────────────────────────────────────────────────────────
    # Architecture Hook 3: ML Session Metadata (AI Agent Interface)
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def get_session_metadata(cls, doc_id: int) -> Dict[str, Any]:
        """
        ML Session Metadata Hook.
        Returns a structured, serializable dict describing the full ML session:
        - Active model details (algorithm, task type, feature columns, metrics)
        - Model Registry comparison summary
        - SHAP explainability status

        This is the single entrypoint AI Agents (Step 10) should call to:
        a) Understand what model was trained
        b) Pick the best run for report narration
        c) Attach SHAP explanations to the report
        d) Invoke predictions programmatically without knowing internal structure
        """
        active_model_path = os.path.join(MODEL_DIR, f"model_{doc_id}.joblib")
        session: Dict[str, Any] = {
            "doc_id": doc_id,
            "model_trained": False,
            "task_type": None,
            "algorithm": None,
            "target_column": None,
            "feature_columns": [],
            "metrics": {},
            "feature_importance": [],
            "shap_available": False,
            "model_comparison": {},
            "agent_instructions": (
                "Use get_model_comparison() to pick the best run. "
                "Use make_prediction() with feature_columns keys for inference. "
                "Use get_shap_explanation() to narrate which features drove the prediction."
            )
        }

        if not os.path.exists(active_model_path) or joblib is None:
            return session

        try:
            payload = joblib.load(active_model_path)
            session["model_trained"] = True
            session["task_type"] = payload.get("task_type")
            session["algorithm"] = payload.get("algorithm", "unknown")
            session["target_column"] = payload.get("target_column")
            session["feature_columns"] = payload.get("feature_columns", [])
            session["metrics"] = payload.get("metrics", {})
            session["feature_importance"] = payload.get("feature_importance", [])
        except Exception as e:
            logger.warning(f"Could not load active model for session metadata: {e}")

        # Attach comparison
        session["model_comparison"] = cls.get_model_comparison(doc_id)

        # Attach SHAP status
        shap_data = cls.get_shap_explanation(doc_id)
        session["shap_available"] = shap_data.get("available", False)
        if shap_data.get("available"):
            session["shap_summary"] = shap_data.get("summary", [])

        return session


def train_test_split(X, y, test_ratio_test=0.2, random_state=42):
    # Standard fallback split implementation if sklearn import somehow breaks
    from sklearn.model_selection import train_test_split as sk_split
    return sk_split(X, y, test_size=test_ratio_test, random_state=random_state)
