"use client";

import React, { useState, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { KnowledgeDocument } from "../types/chat";
import { 
  Brain, FileSpreadsheet, Play, Activity, 
  Settings, Loader2, ArrowLeft, HelpCircle, 
  Sliders, Sparkles, AlertCircle, Compass, 
  CheckCircle2, Gauge, Award, Layers, ChevronLeft, ChevronRight
} from "lucide-react";

interface ColumnOption {
  name: string;
  type: "numeric" | "categorical";
  unique_count: number;
  recommended_target: boolean;
}

interface TrainResult {
  success: boolean;
  task_type: "classification" | "regression";
  metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    r2_score?: number;
    mae?: number;
    mse?: number;
  };
  feature_importance: {
    feature: string;
    importance: number;
  }[];
  classes_count: number;
}

interface PredictionResult {
  task_type: "classification" | "regression";
  prediction: string | number;
  confidence: number;
}

export default function MLArea() {
  const { activeWorkspace, setActiveView } = useChatStore();
  const [panelOpen, setPanelOpen] = useState(true);

  // Document states
  const [spreadsheets, setSpreadsheets] = useState<KnowledgeDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  // Column scanning states
  const [columns, setColumns] = useState<ColumnOption[]>([]);
  const [isLoadingColumns, setIsLoadingColumns] = useState(false);

  // Training parameters
  const [targetCol, setTargetCol] = useState("");
  const [featureCols, setFeatureCols] = useState<string[]>([]);
  const [algorithm, setAlgorithm] = useState("random_forest");

  // Training results
  const [isTraining, setIsTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<TrainResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Prediction states
  const [predictInputs, setPredictInputs] = useState<Record<string, string>>({});
  const [isPredicting, setIsPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  // 1. Fetch spreadsheet files across all knowledge bases of the workspace
  useEffect(() => {
    if (!activeWorkspace) return;

    setIsLoadingDocs(true);
    setSpreadsheets([]);
    setSelectedDoc(null);
    setColumns([]);
    setTrainResult(null);
    setPrediction(null);

    apiService.fetchKnowledgeBases(activeWorkspace.id)
      .then(async (bases) => {
        const allDocs: KnowledgeDocument[] = [];
        for (const kb of bases) {
          const docs = await apiService.fetchDocuments(kb.id);
          const sheets = docs.filter(doc => 
            doc.filename.endsWith(".csv") || 
            doc.filename.endsWith(".xlsx") || 
            doc.filename.endsWith(".xls") ||
            doc.mime_type.includes("csv") ||
            doc.mime_type.includes("spreadsheet") ||
            doc.mime_type.includes("excel")
          );
          allDocs.push(...sheets);
        }
        const uniqueDocs = allDocs.filter((v, i, a) => a.findIndex(t => t.id === v.id) === i);
        setSpreadsheets(uniqueDocs);
      })
      .catch(err => {
        console.error("Failed to load documents for ML:", err);
      })
      .finally(() => {
        setIsLoadingDocs(false);
      });
  }, [activeWorkspace]);

  // 2. Fetch column profiling options when doc changes
  useEffect(() => {
    if (!selectedDoc) {
      setColumns([]);
      setTargetCol("");
      setFeatureCols([]);
      setTrainResult(null);
      setPrediction(null);
      return;
    }

    setIsLoadingColumns(true);
    setErrorMsg(null);
    setColumns([]);
    setTrainResult(null);
    setPrediction(null);

    apiService.apiClient.get<{ columns: ColumnOption[] }>(`/ml/options/${selectedDoc.id}`)
      .then(res => {
        const cols = res.data.columns || [];
        setColumns(cols);

        // Pre-select recommended target
        const rec = cols.find(c => c.recommended_target);
        if (rec) {
          setTargetCol(rec.name);
          setFeatureCols(cols.filter(c => c.name !== rec.name).map(c => c.name));
        } else if (cols.length > 0) {
          setTargetCol(cols[cols.length - 1].name);
          setFeatureCols(cols.slice(0, cols.length - 1).map(c => c.name));
        }
      })
      .catch(err => {
        console.error("Failed to scan CSV columns:", err);
        setErrorMsg("Failed to read tabular columns. Ensure the CSV delimiter is correct.");
      })
      .finally(() => {
        setIsLoadingColumns(false);
      });
  }, [selectedDoc]);

  // Initialize input state when model finishes training
  useEffect(() => {
    if (!trainResult) {
      setPredictInputs({});
      setPrediction(null);
      return;
    }
    const initInputs: Record<string, string> = {};
    featureCols.forEach(col => {
      initInputs[col] = "";
    });
    setPredictInputs(initInputs);
    setPrediction(null);
  }, [trainResult, featureCols]);

  const handleTrain = () => {
    if (!selectedDoc || !targetCol || featureCols.length === 0) return;

    setIsTraining(true);
    setErrorMsg(null);
    setTrainResult(null);
    setPrediction(null);

    apiService.apiClient.post<TrainResult>(`/ml/train/${selectedDoc.id}`, {
      target_column: targetCol,
      feature_columns: featureCols,
      algorithm: algorithm
    })
      .then(res => {
        setTrainResult(res.data);
      })
      .catch(err => {
        console.error("Training failed:", err);
        setErrorMsg(err.response?.data?.detail || "ML model training failed. Verify selected columns have numeric properties.");
      })
      .finally(() => {
        setIsTraining(false);
      });
  };

  const handlePredict = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;

    setIsPredicting(true);
    setPredictError(null);
    setPrediction(null);

    apiService.apiClient.post<PredictionResult>(`/ml/predict/${selectedDoc.id}`, {
      inputs: predictInputs
    })
      .then(res => {
        setPrediction(res.data);
      })
      .catch(err => {
        console.error("Prediction failed:", err);
        setPredictError(err.response?.data?.detail || "Prediction error. Fill all features with valid numeric values.");
      })
      .finally(() => {
        setIsPredicting(false);
      });
  };

  const toggleFeatureCol = (colName: string) => {
    if (featureCols.includes(colName)) {
      setFeatureCols(featureCols.filter(x => x !== colName));
    } else {
      setFeatureCols([...featureCols, colName]);
    }
  };

  const handleTargetChange = (name: string) => {
    setTargetCol(name);
    // Remove new target from features if present
    setFeatureCols(featureCols.filter(x => x !== name));
  };

  return (
    <div className="relative flex h-full w-full text-[#f4f4f5] overflow-hidden bg-transparent">
      
      {/* Left panel: Spreadsheet File Select */}
      <div 
        className="flex-shrink-0 flex flex-col justify-between" 
        style={{ 
          width: panelOpen ? "320px" : "0px",
          opacity: panelOpen ? 1 : 0,
          pointerEvents: panelOpen ? "auto" : "none",
          background: "var(--panel-bg)", 
          borderRight: panelOpen ? "1px solid var(--border)" : "none", 
          backdropFilter: "blur(12px)",
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
        }}
      >
        <div className="p-6 overflow-y-auto flex-1 space-y-6 min-w-[320px]">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-500" />
            <h2 className="text-lg font-bold text-white">ML Studio</h2>
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Select Dataset CSV
            </label>
            {isLoadingDocs ? (
              <div className="flex items-center gap-2 text-zinc-500 text-xs py-4">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-500" />
                <span>Scanning document nodes...</span>
              </div>
            ) : spreadsheets.length === 0 ? (
              <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/10 text-center text-xs text-zinc-500">
                No CSV files uploaded. Go to Knowledge Base to upload spreadsheet files.
              </div>
            ) : (
              <div className="space-y-2">
                {spreadsheets.map((doc) => (
                  <div 
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className={`flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition ${
                      selectedDoc?.id === doc.id 
                        ? "border-indigo-500 bg-indigo-500/5 text-white" 
                        : "border-zinc-800 bg-zinc-900/20 hover:bg-zinc-900/40 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <FileSpreadsheet className="h-5 w-5 text-indigo-400 shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate leading-tight">{doc.filename}</p>
                      <p className="text-[10px] text-zinc-500 mt-1 font-mono">{formatSize(doc.size)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-zinc-800">
          <button 
            onClick={() => setActiveView("chat")}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-sm font-semibold text-zinc-300 hover:text-white transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Chat Workspace
          </button>
        </div>
      </div>

      {/* Floating Collapse Trigger */}
      <button
        onClick={() => setPanelOpen(!panelOpen)}
        className="absolute top-6 z-30 flex h-6 w-6 items-center justify-center rounded-full text-zinc-500 hover:text-indigo-400 shadow-lg transition-all"
        style={{ 
          left: panelOpen ? "308px" : "12px", 
          background: "var(--input-bg)", 
          border: "1px solid var(--border)",
          transition: "left 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
        }}
        title={panelOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {panelOpen ? <ChevronLeft className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
      </button>

      {/* Main ML Studio Workspace */}
      <div className="flex-1 overflow-y-auto bg-zinc-900/10 p-8">
        {isLoadingColumns ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Loader2 className="h-12 w-12 text-indigo-500 animate-spin mb-4" />
            <h3 className="text-base font-semibold text-white">Scanning Dataset Columns</h3>
            <p className="text-xs text-zinc-500 mt-1">Pre-processing schemas and looking for classification labels...</p>
          </div>
        ) : errorMsg ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
            <AlertCircle className="h-12 w-12 text-red-500 mb-4 animate-bounce" />
            <h3 className="text-base font-semibold text-white">ML Column scan failed</h3>
            <p className="text-xs text-red-400/90 leading-relaxed mt-2">{errorMsg}</p>
            <button 
              onClick={() => selectedDoc && setSelectedDoc({ ...selectedDoc })}
              className="mt-6 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white rounded-lg transition"
            >
              Retry Pre-processing
            </button>
          </div>
        ) : selectedDoc && columns.length > 0 ? (
          <div className="max-w-5xl w-full mx-auto space-y-8">
            
            {/* Page Header */}
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Machine Learning Model Builder</h1>
              <p className="text-xs text-zinc-400 mt-1">
                Selected dataset: <strong className="text-indigo-400">{selectedDoc.filename}</strong>. Train classifiers or regressors locally.
              </p>
            </div>

            {/* Config row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Columns Selector Checklist */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/30 lg:col-span-2 space-y-4">
                <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
                  <Sliders className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Configure Features & Targets</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                  
                  {/* Feature columns select */}
                  <div className="space-y-3">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                      Predictor Features (Input columns)
                    </label>
                    <div className="border border-zinc-850 rounded-xl bg-zinc-950/40 p-3 max-h-[220px] overflow-y-auto space-y-2">
                      {columns.map(col => {
                        const disabled = col.name === targetCol;
                        return (
                          <div 
                            key={col.name}
                            onClick={() => !disabled && toggleFeatureCol(col.name)}
                            className={`flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer transition ${
                              disabled 
                                ? "border-zinc-900 bg-zinc-950/20 text-zinc-700 cursor-not-allowed" 
                                : featureCols.includes(col.name)
                                  ? "border-indigo-500 bg-indigo-500/5 text-white font-semibold"
                                  : "border-zinc-850 bg-zinc-900/10 text-zinc-400 hover:text-zinc-200"
                            }`}
                          >
                            <span className="truncate">{col.name}</span>
                            <span className="text-[10px] text-zinc-500 font-mono italic">{col.type}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Target Column select */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                        Target Variable (Column to predict)
                      </label>
                      <select
                        value={targetCol}
                        onChange={(e) => handleTargetChange(e.target.value)}
                        className="w-full text-xs rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-2.5 text-white outline-none focus:border-indigo-500 transition"
                      >
                        {columns.map(col => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.type === "numeric" ? "Numeric" : "Categorical"})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                        Model Training Algorithm
                      </label>
                      <select
                        value={algorithm}
                        onChange={(e) => setAlgorithm(e.target.value)}
                        className="w-full text-xs rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-2.5 text-white outline-none focus:border-indigo-500 transition"
                      >
                        <option value="random_forest">Random Forest Ensemble (Recommended)</option>
                        <option value="gradient_boosting">Gradient Boosting Machines (GBM)</option>
                        <option value="linear">Linear / Logistic Regression</option>
                      </select>
                    </div>
                  </div>

                </div>
              </div>

              {/* Training Action Card */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/20 lg:col-span-1 flex flex-col justify-between">
                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                    <Compass className="h-4 w-4 text-indigo-400" />
                    Auto Model Scanner
                  </h3>
                  
                  {/* Recommended Target explanations */}
                  <div className="p-4 rounded-xl border border-indigo-500/10 bg-indigo-500/5 text-xs leading-normal text-zinc-400 space-y-1.5">
                    <p className="font-bold text-indigo-400 flex items-center gap-1">
                      <Sparkles className="h-3.5 w-3.5" />
                      Auto-Target suggestion
                    </p>
                    <p>
                      We recommend selecting column fields like <strong className="text-white">"{targetCol}"</strong> to train classifiers.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleTrain}
                  disabled={isTraining || featureCols.length === 0}
                  className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition shadow-md mt-6 ${
                    isTraining || featureCols.length === 0
                      ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                      : "bg-indigo-600 hover:bg-indigo-500 text-white"
                  }`}
                >
                  {isTraining ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Fitting Model Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      <span>Train Machine Learning Model</span>
                    </>
                  )}
                </button>
              </div>

            </div>

            {/* Model Evaluation Dashboard (R2, F1 dial metrics, Importance chart) */}
            {trainResult && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Metrics Dial Panel */}
                <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/20 lg:col-span-1 space-y-5">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                    <Gauge className="h-4 w-4 text-indigo-400" />
                    Model Validation Metrics
                  </h3>

                  <div className="flex flex-col items-center justify-center py-4 relative">
                    <Award className="h-12 w-12 text-amber-500 mb-2 animate-bounce" />
                    <h4 className="text-2xl font-bold text-white tracking-tight">
                      {trainResult.task_type === "classification" 
                        ? `${(trainResult.metrics.accuracy! * 100).toFixed(1)}%`
                        : `R² = ${trainResult.metrics.r2_score!.toFixed(3)}`
                      }
                    </h4>
                    <p className="text-[10px] text-zinc-500 uppercase font-bold mt-1 tracking-wider">
                      {trainResult.task_type === "classification" ? "Training Accuracy" : "R-Squared Score"}
                    </p>
                  </div>

                  <div className="border-t border-zinc-800/80 pt-4 text-xs space-y-3.5">
                    {trainResult.task_type === "classification" ? (
                      <>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Precision (Macro)</span>
                          <span className="text-white font-semibold font-mono">{trainResult.metrics.precision}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Recall (Macro)</span>
                          <span className="text-white font-semibold font-mono">{trainResult.metrics.recall}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">F1-Score (Macro)</span>
                          <span className="text-white font-semibold font-mono">{trainResult.metrics.f1_score}</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Mean Absolute Error (MAE)</span>
                          <span className="text-white font-semibold font-mono">{trainResult.metrics.mae?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Mean Squared Error (MSE)</span>
                          <span className="text-white font-semibold font-mono">{trainResult.metrics.mse?.toLocaleString()}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Feature Importance SVG Graph */}
                <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/20 lg:col-span-2 space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                    <Layers className="h-4 w-4 text-indigo-400" />
                    Feature Importance Graph (Transformed Columns Correlation)
                  </h3>

                  <div className="space-y-3.5 pt-2">
                    {trainResult.feature_importance.slice(0, 5).map((fi, idx) => {
                      const pct = Math.max(fi.importance * 100, 1.5);
                      return (
                        <div key={idx} className="space-y-1.5 text-xs">
                          <div className="flex justify-between text-zinc-400">
                            <span className="font-semibold text-zinc-300">{fi.feature}</span>
                            <span className="font-mono text-[10px] text-zinc-500">{(fi.importance * 100).toFixed(1)}% influence</span>
                          </div>
                          <div className="h-2.5 w-full rounded-full bg-zinc-900 overflow-hidden border border-zinc-850">
                            <div 
                              className="h-full bg-gradient-to-r from-indigo-600 to-violet-500 rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            )}

            {/* Dynamic Prediction Forms */}
            {trainResult && (
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/20 space-y-6">
                <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
                  <Activity className="h-4 w-4 text-emerald-400 animate-pulse" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Live Predictor Inference Playground</h3>
                </div>

                <form onSubmit={handlePredict} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
                  {featureCols.map(col => {
                    const colOpt = columns.find(c => c.name === col);
                    return (
                      <div key={col} className="space-y-1.5">
                        <label className="block text-zinc-500 font-semibold uppercase">{col}</label>
                        <input
                          type={colOpt?.type === "numeric" ? "number" : "text"}
                          step="any"
                          required
                          value={predictInputs[col] || ""}
                          onChange={(e) => setPredictInputs({ ...predictInputs, [col]: e.target.value })}
                          placeholder={colOpt?.type === "numeric" ? "Input number (e.g. 14.5)" : "Input text category"}
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3.5 py-2.5 text-white outline-none focus:border-indigo-500 transition"
                        />
                      </div>
                    );
                  })}

                  <div className="lg:col-span-3 flex justify-end pt-4 border-t border-zinc-850 gap-4 items-center">
                    {predictError && (
                      <p className="text-[10px] text-red-400 font-semibold animate-pulse">{predictError}</p>
                    )}
                    <button
                      type="submit"
                      disabled={isPredicting}
                      className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white rounded-xl transition flex items-center gap-1.5 shadow-md"
                    >
                      {isPredicting ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Computing Inference...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Predict Output</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>

                {/* Inference Results output */}
                {prediction && (
                  <div className="p-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <p className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Model Inference Output</p>
                      <h3 className="text-2xl font-bold text-white mt-1.5 tracking-tight font-mono">{prediction.prediction}</h3>
                    </div>
                    {prediction.task_type === "classification" && (
                      <div className="text-right">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">Predict Confidence</span>
                        <span className="text-emerald-400 font-mono font-bold text-lg">{(prediction.confidence * 100).toFixed(1)}% Prob</span>
                      </div>
                    )}
                  </div>
                )}

              </div>
            )}

          </div>
        ) : (
          <div className="flex-grow flex flex-col items-center justify-center p-8 text-center max-w-sm mx-auto h-[70vh]">
            <div className="h-16 w-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-500 border border-indigo-500/20 mb-6 animate-pulse">
              <Brain className="h-8 w-8" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2">Select Dataset for ML Studio</h2>
            <p className="text-zinc-500 text-xs leading-relaxed">
              Choose an uploaded spreadsheet or CSV from the sidebar. Select your features and training targets. The ML studio will train Random Forests or Boosting ensembles, output validation scores, and create live prediction models!
            </p>
          </div>
        )}
      </div>

    </div>
  );
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};
