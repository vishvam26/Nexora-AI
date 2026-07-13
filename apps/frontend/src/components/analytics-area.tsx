"use client";

import React, { useState, useEffect, useRef } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { KnowledgeDocument } from "../types/chat";
import { 
  BarChart3, FileSpreadsheet, AlertTriangle, Lightbulb, 
  HelpCircle, RefreshCw, Loader2, ArrowLeft, Download, 
  Sparkles, FileText, CheckCircle2, Table, LineChart, 
  Info, Grid, ChevronLeft, ChevronRight
} from "lucide-react";

interface NumericStats {
  mean: number;
  median: number;
  mode: number;
  std_dev: number;
  variance: number;
  skewness: number;
  kurtosis: number;
  quartiles: {
    q25: number;
    q50: number;
    q75: number;
  };
}

interface OutlierReport {
  count: number;
  percentage: number;
  threshold_low: number;
  threshold_high: number;
  sample_outliers: number[];
}

interface DatasetProfile {
  document_id: number;
  rows_count: number;
  columns_count: number;
  columns: {
    name: string;
    type: "numeric" | "categorical" | "datetime";
    dtype: string;
    missing_count: number;
    missing_pct: number;
    unique_count: number;
  }[];
  descriptive_stats: Record<string, NumericStats>;
  outlier_reports: Record<string, OutlierReport>;
  correlation_matrix: Record<string, Record<string, number>>;
  quality_report: {
    duplicate_rows: number;
    duplicate_pct: number;
    total_cells: number;
    missing_cells: number;
    missing_pct: number;
    warnings: string[];
  };
  imputation_recommendations: {
    column: string;
    pct: number;
    recommendation: string;
  }[];
  kpis: {
    label: string;
    value: string;
    desc: string;
  }[];
  chart_recommendations: {
    x_column: string;
    y_column: string;
    chart_type: "bar" | "line" | "scatter" | "pie";
    reason: string;
  }[];
  preview_rows: Record<string, any>[];
}

interface ChartItem {
  label: string;
  value: number;
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

export default function AnalyticsArea() {
  const { activeWorkspace, setActiveView } = useChatStore();
  const [panelOpen, setPanelOpen] = useState(true);

  // Documents listing states
  const [spreadsheets, setSpreadsheets] = useState<KnowledgeDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  // Profile profiling states
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // AI insights states
  const [insights, setInsights] = useState("");
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [insightFocus, setInsightFocus] = useState("");

  // Chart configuration states
  const [chartType, setChartType] = useState<"bar" | "line" | "scatter">("bar");
  const [xCol, setXCol] = useState("");
  const [yCol, setYCol] = useState("");
  const [aggType, setAggType] = useState("sum");
  const [chartData, setChartData] = useState<ChartItem[]>([]);
  const [isLoadingChart, setIsLoadingChart] = useState(false);

  const chartSvgRef = useRef<SVGSVGElement>(null);

  // 1. Fetch spreadsheet files across all knowledge bases of the workspace
  useEffect(() => {
    if (!activeWorkspace) return;

    setIsLoadingDocs(true);
    setSpreadsheets([]);
    setSelectedDoc(null);
    setProfile(null);
    setChartData([]);
    setInsights("");

    apiService.fetchKnowledgeBases(activeWorkspace.id)
      .then(async (bases) => {
        const allDocs: KnowledgeDocument[] = [];
        for (const kb of bases) {
          const docs = await apiService.fetchDocuments(kb.id);
          // Filter CSV or Excel spreadsheets
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
        
        // Remove duplicates if doc exists in multiple lists
        const uniqueDocs = allDocs.filter((v, i, a) => a.findIndex(t => t.id === v.id) === i);
        setSpreadsheets(uniqueDocs);
      })
      .catch(err => {
        console.error("Failed to load documents for analytics:", err);
      })
      .finally(() => {
        setIsLoadingDocs(false);
      });
  }, [activeWorkspace]);

  // 2. Fetch EDA profile when document changes
  useEffect(() => {
    if (!selectedDoc) {
      setProfile(null);
      setChartData([]);
      setInsights("");
      return;
    }

    setIsLoadingProfile(true);
    setErrorMsg(null);
    setProfile(null);
    setChartData([]);
    setInsights("");

    apiService.apiClient.get<DatasetProfile>(`/analytics/profile/${selectedDoc.id}`)
      .then(res => {
        const prof = res.data;
        setProfile(prof);

        // Apply AI Chart recommendations
        if (prof.chart_recommendations && prof.chart_recommendations.length > 0) {
          const rec = prof.chart_recommendations[0];
          setXCol(rec.x_column);
          setYCol(rec.y_column);
          // Scatter uses scatter, others map to bar/line
          setChartType(rec.chart_type === "scatter" ? "scatter" : rec.chart_type === "line" ? "line" : "bar");
        } else if (prof.columns && prof.columns.length > 1) {
          // Fallback to first numeric and first categorical
          const numeric = prof.columns.find(c => c.type === "numeric")?.name || "";
          const categorical = prof.columns.find(c => c.type === "categorical")?.name || prof.columns[0].name;
          setXCol(categorical);
          setYCol(numeric);
          setChartType("bar");
        }

        // Generate AI insights automatically on load
        triggerAIInsights(prof);
      })
      .catch(err => {
        console.error("Failed to profile dataset:", err);
        setErrorMsg(err.response?.data?.detail || "Tabular analysis failed. Make sure the CSV file has a clean layout.");
      })
      .finally(() => {
        setIsLoadingProfile(false);
      });
  }, [selectedDoc]);

  // 3. Fetch aggregated chart data when coordinates or aggregation type changes
  useEffect(() => {
    if (!selectedDoc || !xCol || !yCol) return;

    setIsLoadingChart(true);
    apiService.apiClient.post<ChartItem[]>(`/analytics/chart/${selectedDoc.id}`, {
      x_column: xCol,
      y_column: yCol,
      aggregation: aggType
    })
      .then(res => {
        setChartData(res.data || []);
      })
      .catch(err => {
        console.error("Failed to generate aggregates:", err);
        setChartData([]);
      })
      .finally(() => {
        setIsLoadingChart(false);
      });
  }, [selectedDoc, xCol, yCol, aggType]);

  const triggerAIInsights = (targetProfile: DatasetProfile, query: string = "") => {
    if (!selectedDoc || !targetProfile) return;

    setIsLoadingInsights(true);
    apiService.apiClient.post<{ insights: string }>(`/analytics/insights/${selectedDoc.id}`, {
      query: query || null
    })
      .then(res => {
        setInsights(res.data.insights || "No insights returned.");
      })
      .catch(err => {
        console.error("AI Insights failed:", err);
        setInsights("Failed to compile AI insights.");
      })
      .finally(() => {
        setIsLoadingInsights(false);
      });
  };

  // Exporters
  const exportToCSV = () => {
    if (!profile) return;
    
    // Create detailed CSV summary sheet of descriptive stats
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Nexora Descriptive Statistics Report\n";
    csvContent += `Document ID,${profile.document_id}\n`;
    csvContent += `Total Rows,${profile.rows_count}\n`;
    csvContent += `Total Columns,${profile.columns_count}\n\n`;
    
    csvContent += "Column Name,Mean,Median,Mode,Std Dev,Variance,Skewness,Kurtosis,Q25,Q50,Q75\n";
    
    Object.entries(profile.descriptive_stats).forEach(([col, stats]) => {
      csvContent += `"${col}",${stats.mean},${stats.median},${stats.mode},${stats.std_dev},${stats.variance},${stats.skewness},${stats.kurtosis},${stats.quartiles.q25},${stats.quartiles.q50},${stats.quartiles.q75}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `statistics_report_doc_${selectedDoc?.id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToPNG = () => {
    if (!chartSvgRef.current) return;
    
    try {
      const svgElement = chartSvgRef.current;
      const svgString = new XMLSerializer().serializeToString(svgElement);
      const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
      const URL = window.URL || window.webkitURL || window;
      const blobURL = URL.createObjectURL(svgBlob);
      
      const image = new Image();
      image.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = svgElement.clientWidth * 2; // high res
        canvas.height = svgElement.clientHeight * 2;
        
        const context = canvas.getContext("2d");
        if (context) {
          // Draw dark background matching theme
          context.fillStyle = "#0c0c0e";
          context.fillRect(0, 0, canvas.width, canvas.height);
          
          context.drawImage(image, 0, 0, canvas.width, canvas.height);
          
          const pngUri = canvas.toDataURL("image/png");
          const link = document.createElement("a");
          link.href = pngUri;
          link.download = `chart_export_doc_${selectedDoc?.id}.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      };
      image.src = blobURL;
    } catch (e) {
      console.error("Failed to export PNG:", e);
    }
  };

  const exportToPPT = () => {
    if (!profile) return;
    
    // Create text structured presentation deck slide script
    let pptContent = "NEXORA ANALYTICS ENGINE PRESENTATION SLIDES\n";
    pptContent += "========================================\n\n";
    pptContent += "SLIDE 1: DATASET PROFILE OVERVIEW\n";
    pptContent += ` - File: ${selectedDoc?.filename}\n`;
    pptContent += ` - Rows: ${profile.rows_count} | Columns: ${profile.columns_count}\n`;
    pptContent += ` - Cells Count: ${profile.quality_report.total_cells}\n`;
    pptContent += ` - Missing Cells: ${profile.quality_report.missing_cells} (${profile.quality_report.missing_pct}%)\n\n`;
    
    pptContent += "SLIDE 2: DESCRIPTIVE STATISTICS BRIEF\n";
    Object.entries(profile.descriptive_stats).slice(0, 3).forEach(([col, stats]) => {
      pptContent += ` * ${col}:\n`;
      pptContent += `   - Mean: ${stats.mean} | Median: ${stats.median}\n`;
      pptContent += `   - Std Dev: ${stats.std_dev} | Kurtosis: ${stats.kurtosis}\n`;
    });
    pptContent += "\n";
    
    pptContent += "SLIDE 3: DATASET QUALITY & CORRELATION WARNINGS\n";
    profile.quality_report.warnings.forEach(w => {
      pptContent += ` - [Warning] ${w}\n`;
    });
    pptContent += "\n";

    pptContent += "SLIDE 4: AI SUMMARY BUSINESS INSIGHTS\n";
    pptContent += insights || "No insights processed.\n";

    const blob = new Blob([pptContent], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = `presentation_summary_doc_${selectedDoc?.id}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Rendering Helper for custom responsive SVGs
  const renderSVGChart = () => {
    if (chartData.length === 0) return null;

    const width = 600;
    const height = 300;
    const padding = 50;

    const values = chartData.map(d => d.value);
    const maxValue = Math.max(...values, 1);
    const minValue = Math.min(...values, 0);

    const getX = (index: number) => {
      return padding + (index * (width - padding * 2)) / Math.max(chartData.length - 1, 1);
    };

    const getY = (val: number) => {
      const scale = (height - padding * 2) / (maxValue - minValue);
      return height - padding - (val - minValue) * scale;
    };

    if (chartType === "bar") {
      const barWidth = Math.max((width - padding * 2) / chartData.length * 0.6, 10);
      const spacing = (width - padding * 2) / chartData.length;
      
      return chartData.map((d, i) => {
        const x = padding + i * spacing + (spacing - barWidth) / 2;
        const y = getY(d.value);
        const barHeight = Math.max(height - padding - y, 5);

        return (
          <g key={i} className="group">
            {/* Bar with gradient glow fill */}
            <defs>
              <linearGradient id={`barGlow-${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8"/>
                <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.1"/>
              </linearGradient>
            </defs>
            <rect 
              x={x} 
              y={y} 
              width={barWidth} 
              height={barHeight} 
              fill={`url(#barGlow-${i})`}
              rx={4}
              className="hover:fill-indigo-400 transition-colors duration-200 cursor-pointer"
            />
            {/* Tooltip Hover value */}
            <text 
              x={x + barWidth / 2} 
              y={y - 8} 
              textAnchor="middle" 
              fill="#c084fc" 
              fontSize={10} 
              fontWeight="bold"
              className="opacity-0 group-hover:opacity-100 transition-opacity font-mono"
            >
              {d.value.toLocaleString()}
            </text>
            {/* X-axis Label */}
            <text 
              x={x + barWidth / 2} 
              y={height - padding + 18} 
              textAnchor="middle" 
              fill="#71717a" 
              fontSize={9} 
              transform={`rotate(15, ${x + barWidth / 2}, ${height - padding + 18})`}
              className="font-medium"
            >
              {d.label.length > 8 ? `${d.label.slice(0, 7)}...` : d.label}
            </text>
          </g>
        );
      });
    }

    if (chartType === "line") {
      const points = chartData.map((d, i) => `${getX(i)},${getY(d.value)}`).join(" ");
      return (
        <g>
          {/* Line Path */}
          <polyline 
            fill="none" 
            stroke="#6366f1" 
            strokeWidth={3.5} 
            points={points} 
            strokeLinecap="round"
            filter="drop-shadow(0px 4px 10px rgba(99, 102, 241, 0.4))"
          />
          {chartData.map((d, i) => {
            const x = getX(i);
            const y = getY(d.value);
            return (
              <g key={i} className="group">
                <circle 
                  cx={x} 
                  cy={y} 
                  r={5} 
                  fill="#ffffff" 
                  stroke="#4f46e5" 
                  strokeWidth={3} 
                  className="cursor-pointer hover:scale-125 transition-transform" 
                />
                <text 
                  x={x} 
                  y={y - 12} 
                  textAnchor="middle" 
                  fill="#c084fc" 
                  fontSize={10} 
                  fontWeight="bold"
                  className="opacity-0 group-hover:opacity-100 transition-opacity font-mono"
                >
                  {d.value.toLocaleString()}
                </text>
                <text 
                  x={x} 
                  y={height - padding + 18} 
                  textAnchor="middle" 
                  fill="#71717a" 
                  fontSize={9}
                >
                  {d.label.length > 8 ? `${d.label.slice(0, 7)}...` : d.label}
                </text>
              </g>
            );
          })}
        </g>
      );
    }

    return null;
  };

  return (
    <div className="relative flex h-full w-full text-[#f4f4f5] overflow-hidden bg-transparent">
      
      {/* Left panel: File Selector */}
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
            <BarChart3 className="h-5 w-5 text-indigo-500" />
            <h2 className="text-lg font-bold text-white">Analytics Engine</h2>
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Select Dataset CSV/Spreadsheet
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

      {/* Main dashboard panel */}
      <div className="flex-1 overflow-y-auto bg-zinc-900/10 p-8">
        {isLoadingProfile ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Loader2 className="h-12 w-12 text-indigo-500 animate-spin mb-4" />
            <h3 className="text-base font-semibold text-white">Running Exploratory Data Analysis (EDA)</h3>
            <p className="text-xs text-zinc-500 mt-1">Pandas is computing descriptive metrics, Pearson correlations, and outlier ranges...</p>
          </div>
        ) : errorMsg ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
            <AlertTriangle className="h-12 w-12 text-red-500 mb-4 animate-bounce" />
            <h3 className="text-base font-semibold text-white">Tabular Parsing Error</h3>
            <p className="text-xs text-red-400/90 leading-relaxed mt-2">{errorMsg}</p>
            <button 
              onClick={() => selectedDoc && setSelectedDoc({ ...selectedDoc })}
              className="mt-6 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white rounded-lg transition"
            >
              Retry Profile Analysis
            </button>
          </div>
        ) : profile ? (
          <div className="max-w-5xl w-full mx-auto space-y-8">
            
            {/* Header dashboard controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/80 pb-6">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">{selectedDoc?.filename}</h1>
                <p className="text-xs text-zinc-400 mt-1">
                  Dataset dimensions: <strong className="text-indigo-400">{profile.rows_count}</strong> rows &times; <strong className="text-indigo-400">{profile.columns_count}</strong> columns
                </p>
              </div>

              {/* Document exporters buttons */}
              <div className="flex items-center gap-2">
                <button 
                  onClick={exportToCSV}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-850 bg-zinc-950 text-xs font-semibold text-zinc-400 hover:text-white transition"
                  title="Export Statistics Summary as Excel/CSV"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Excel
                </button>
                <button 
                  onClick={exportToPNG}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-850 bg-zinc-950 text-xs font-semibold text-zinc-400 hover:text-white transition"
                  title="Export Chart Area as Image"
                >
                  <Download className="h-3.5 w-3.5" />
                  PNG
                </button>
                <button 
                  onClick={exportToPPT}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-850 bg-zinc-950 text-xs font-semibold text-zinc-400 hover:text-white transition"
                  title="Download PowerPoint presentation draft"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  PowerPoint
                </button>
              </div>
            </div>

            {/* Dashboard KPIs metrics row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {profile.kpis.map((kpi, kIdx) => (
                <div key={kIdx} className="p-5 rounded-2xl border border-zinc-800/60 bg-zinc-950/40 relative overflow-hidden">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider leading-none">{kpi.label}</p>
                  <h3 className="text-xl font-bold text-white mt-2 tracking-tight">{kpi.value}</h3>
                  <p className="text-[10px] text-zinc-600 mt-1 leading-normal">{kpi.desc}</p>
                </div>
              ))}
            </div>

            {/* Quality Summary & Missing Recommendations Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 lg:col-span-1 space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Dataset Quality Card
                </h3>
                <div className="space-y-3.5 text-sm pt-2">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Duplicate Rows</span>
                    <span className="text-white font-semibold">{profile.quality_report.duplicate_rows} ({profile.quality_report.duplicate_pct}%)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Total Cell Blocks</span>
                    <span className="text-white font-semibold">{profile.quality_report.total_cells.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Missing Cell Blocks</span>
                    <span className="text-white font-semibold">{profile.quality_report.missing_cells.toLocaleString()} ({profile.quality_report.missing_pct}%)</span>
                  </div>
                </div>
                {profile.quality_report.warnings.length > 0 && (
                  <div className="mt-4 p-3.5 rounded-xl border border-red-500/10 bg-red-500/5 space-y-1.5">
                    <p className="text-[10px] uppercase font-bold text-red-400 flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Dataset Warnings
                    </p>
                    <ul className="list-disc pl-4 text-[10px] text-red-400/90 space-y-1">
                      {profile.quality_report.warnings.map((w, wIdx) => (
                        <li key={wIdx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Data Imputation Recommendations panel */}
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 lg:col-span-2 space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-500" />
                  Data Cleanup Recommendations
                </h3>
                {profile.imputation_recommendations.length === 0 ? (
                  <p className="text-xs text-zinc-500 py-6 italic">Dataset is complete and clean! No missing cells detected.</p>
                ) : (
                  <div className="divide-y divide-zinc-800/60 max-h-[160px] overflow-y-auto pr-2 space-y-3 pt-2">
                    {profile.imputation_recommendations.map((rec, rIdx) => (
                      <div key={rIdx} className="text-xs space-y-1 pt-3 first:pt-0">
                        <span className="font-bold text-white text-[10px] uppercase bg-zinc-800 px-2 py-0.5 rounded mr-2">
                          Column: {rec.column}
                        </span>
                        <p className="text-zinc-400 leading-normal mt-1">{rec.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* descriptive_stats table grid */}
            <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                <Table className="h-4 w-4 text-indigo-400" />
                Descriptive Statistical Profile (Numeric Columns)
              </h3>
              
              {Object.keys(profile.descriptive_stats).length === 0 ? (
                <p className="text-xs text-zinc-500 py-6 italic">No numeric columns found in the selected file to calculate statistics.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/30 text-xs">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-950/40 text-zinc-500 uppercase tracking-wider font-semibold">
                        <th className="py-3 px-4">Column Name</th>
                        <th className="py-3 px-4">Mean</th>
                        <th className="py-3 px-4">Median</th>
                        <th className="py-3 px-4">Std Dev</th>
                        <th className="py-3 px-4">Variance</th>
                        <th className="py-3 px-4">Skewness</th>
                        <th className="py-3 px-4">Kurtosis</th>
                        <th className="py-3 px-4">Quartiles (Q25/Q75)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/80 text-zinc-300 font-mono">
                      {Object.entries(profile.descriptive_stats).map(([col, stats]) => (
                        <tr key={col} className="hover:bg-zinc-900/10 transition-colors">
                          <td className="py-3 px-4 font-sans font-bold text-white">{col}</td>
                          <td className="py-3 px-4">{stats.mean}</td>
                          <td className="py-3 px-4">{stats.median}</td>
                          <td className="py-3 px-4">{stats.std_dev}</td>
                          <td className="py-3 px-4">{stats.variance.toLocaleString()}</td>
                          <td className="py-3 px-4">{stats.skewness}</td>
                          <td className="py-3 px-4">{stats.kurtosis}</td>
                          <td className="py-3 px-4 text-zinc-400">
                            {stats.quartiles.q25} / {stats.quartiles.q75}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Outlier Report & Correlation Heatmap Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Outliers list */}
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                  <Info className="h-4 w-4 text-indigo-400" />
                  Outliers Report (IQR Detection)
                </h3>
                
                {Object.keys(profile.outlier_reports).length === 0 ? (
                  <p className="text-xs text-zinc-500 py-6 italic">No numeric outliers processed.</p>
                ) : (
                  <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                    {Object.entries(profile.outlier_reports).map(([col, report]) => (
                      <div key={col} className="p-4 rounded-xl border border-zinc-850 bg-zinc-950/30 text-xs space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-white">{col}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            report.count > 0 ? "bg-red-500/10 text-red-400 border border-red-500/15" : "bg-green-500/10 text-green-400"
                          }`}>
                            {report.count} Outliers ({report.percentage}%)
                          </span>
                        </div>
                        <div className="text-[10px] text-zinc-500 flex gap-4">
                          <span>Min Threshold: {report.threshold_low}</span>
                          <span>Max Threshold: {report.threshold_high}</span>
                        </div>
                        {report.count > 0 && (
                          <div className="text-[10px] text-zinc-400">
                            <strong>Sample values:</strong> {report.sample_outliers.join(", ")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Correlation Heatmap matrix */}
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                  <Grid className="h-4 w-4 text-indigo-400" />
                  Pearson Correlation Heatmap Matrix
                </h3>

                {Object.keys(profile.correlation_matrix).length === 0 ? (
                  <p className="text-xs text-zinc-500 py-6 italic">Correlation matrix unavailable. Requires 2 or more numeric columns.</p>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="grid gap-1 border border-zinc-800 p-2.5 rounded-xl bg-zinc-950/50" style={{
                      gridTemplateColumns: `repeat(${Object.keys(profile.correlation_matrix).length}, minmax(0, 1fr))`
                    }}>
                      {Object.entries(profile.correlation_matrix).map(([c1, pairings]) => (
                        Object.entries(pairings).map(([c2, coef], cellIdx) => {
                          // Color mapping
                          let color = "bg-zinc-800 text-zinc-400"; // neutral
                          if (coef > 0.4) {
                            // Positive correlation (Red gradient)
                            color = coef > 0.7 ? "bg-red-600 text-white font-bold" : "bg-red-950/60 text-red-300";
                          } else if (coef < -0.4) {
                            // Negative correlation (Blue gradient)
                            color = coef < -0.7 ? "bg-blue-600 text-white font-bold" : "bg-blue-950/60 text-blue-300";
                          }

                          return (
                            <div 
                              key={cellIdx}
                              className={`h-11 w-11 rounded flex flex-col items-center justify-center text-[9px] font-mono select-none cursor-help transition-all ${color}`}
                              title={`Correlation coefficient between "${c1}" and "${c2}" = ${coef.toFixed(4)}`}
                            >
                              <span>{coef.toFixed(2)}</span>
                            </div>
                          );
                        })
                      ))}
                    </div>
                    <div className="flex justify-between w-full max-w-[240px] text-[10px] text-zinc-500 mt-4 px-2">
                      <span className="text-blue-400 font-semibold">-1.0 (Negative)</span>
                      <span className="text-zinc-600">0.0</span>
                      <span className="text-red-400 font-semibold">+1.0 (Positive)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Interactive Charting panel & AI Recommendations */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Controls and AI Rec */}
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 lg:col-span-1 space-y-4 flex flex-col justify-between">
                <div className="space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Chart Settings</h3>
                  
                  {/* Selectors */}
                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="block text-zinc-500 mb-1.5 uppercase font-semibold">X-Axis Column</label>
                      <select 
                        value={xCol}
                        onChange={(e) => setXCol(e.target.value)}
                        className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500"
                      >
                        {profile.columns.map(c => (
                          <option key={c.name} value={c.name}>{c.name} ({c.type})</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-zinc-500 mb-1.5 uppercase font-semibold">Y-Axis Column</label>
                      <select 
                        value={yCol}
                        onChange={(e) => setYCol(e.target.value)}
                        className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500"
                      >
                        {profile.columns.filter(c => c.type === "numeric").map(c => (
                          <option key={c.name} value={c.name}>{c.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-zinc-500 mb-1.5 uppercase font-semibold">Aggregation Type</label>
                      <select 
                        value={aggType}
                        onChange={(e) => setAggType(e.target.value)}
                        className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500"
                      >
                        <option value="sum">Sum</option>
                        <option value="mean">Mean</option>
                        <option value="count">Count (Frequency)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-zinc-500 mb-1.5 uppercase font-semibold">Chart Type</label>
                      <select 
                        value={chartType}
                        onChange={(e) => setChartType(e.target.value as any)}
                        className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500"
                      >
                        <option value="bar">Bar Chart</option>
                        <option value="line">Line Chart</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* AI Recommendation Alert */}
                {profile.chart_recommendations.length > 0 && (
                  <div className="p-4 rounded-xl border border-indigo-500/10 bg-indigo-500/5 text-xs space-y-1.5 mt-4">
                    <p className="font-bold text-indigo-400 flex items-center gap-1.5">
                      <Sparkles className="h-4 w-4" />
                      AI Recommendation
                    </p>
                    <p className="text-zinc-400 leading-normal">{profile.chart_recommendations[0].reason}</p>
                  </div>
                )}
              </div>

              {/* Chart Renderer view */}
              <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 lg:col-span-2 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                    <LineChart className="h-4 w-4 text-indigo-400" />
                    Interactive Visualization Area
                  </h3>
                  {isLoadingChart && <Loader2 className="h-4 w-4 animate-spin text-zinc-500" />}
                </div>

                {chartData.length === 0 ? (
                  <div className="h-[300px] flex items-center justify-center border border-dashed border-zinc-800 rounded-2xl text-xs text-zinc-500">
                    No aggregated chart data could be loaded. Adjust columns selector.
                  </div>
                ) : (
                  <div className="w-full flex justify-center bg-zinc-950/20 p-4 rounded-2xl border border-zinc-800/40">
                    <svg 
                      ref={chartSvgRef}
                      viewBox="0 0 600 300" 
                      width="100%" 
                      height="100%" 
                      className="overflow-visible max-h-[300px]"
                    >
                      {/* Grid background lines */}
                      {[0, 0.25, 0.5, 0.75, 1].map((p, i) => {
                        const y = 50 + p * 200;
                        return (
                          <line 
                            key={i}
                            x1={50} 
                            y1={y} 
                            x2={550} 
                            y2={y} 
                            stroke="#1f1f23" 
                            strokeDasharray="4 4"
                          />
                        );
                      })}
                      
                      {/* X and Y axes */}
                      <line x1={50} y1={50} x2={50} y2={250} stroke="#27272a" strokeWidth={1.5} />
                      <line x1={50} y1={250} x2={550} y2={250} stroke="#27272a" strokeWidth={1.5} />
                      
                      {/* SVG elements */}
                      {renderSVGChart()}
                    </svg>
                  </div>
                )}
              </div>
            </div>

            {/* AI Insights Explanation Panel */}
            <div className="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/20 space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-indigo-400" />
                  AI Statistical Insights
                </h3>
                {isLoadingInsights && <Loader2 className="h-4 w-4 animate-spin text-zinc-500" />}
              </div>

              {isLoadingInsights ? (
                <div className="py-12 text-center text-xs text-zinc-500">
                  Senior Business Analyst is running regression/correlations and writing insights...
                </div>
              ) : insights ? (
                <div className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap pt-2 max-w-4xl">
                  {insights}
                </div>
              ) : (
                <p className="text-xs text-zinc-500 italic py-6">Could not load dataset insights.</p>
              )}

              {/* Refresh Insights / Custom Ask block */}
              <div className="pt-4 flex gap-3 border-t border-zinc-800">
                <input 
                  type="text"
                  value={insightFocus}
                  onChange={(e) => setInsightFocus(e.target.value)}
                  placeholder="Focus AI insights on specific metric (e.g. Sales increase in Q3)..."
                  className="flex-1 rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-2.5 text-xs text-white placeholder-zinc-600 outline-none focus:border-indigo-500 transition"
                />
                <button 
                  onClick={() => triggerAIInsights(profile, insightFocus)}
                  className="px-5 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-xl transition flex items-center gap-1.5"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Refresh
                </button>
              </div>
            </div>

          </div>
        ) : (
          <div className="flex-grow flex flex-col items-center justify-center p-8 text-center max-w-sm mx-auto h-[70vh]">
            <div className="h-16 w-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-500 border border-indigo-500/20 mb-6 animate-pulse">
              <BarChart3 className="h-8 w-8" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2">Select Dataset to Profile</h2>
            <p className="text-zinc-500 text-xs leading-relaxed">
              Choose an uploaded spreadsheet or CSV from the sidebar. The engine will calculate descriptive statistics, check quality metrics, recommend visual charts, and write statistical analysis summaries.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
