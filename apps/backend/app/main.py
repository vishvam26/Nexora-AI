print(">>> MAIN.PY LOADED <<<")
import logging
# Configure physical file logging to capture all backend warnings, errors, and exceptions outside watched folder
import os
log_path = "backend.log"
if os.name == "nt":
    local_path = "C:/Users/vishv/.gemini/antigravity-ide/brain/ba311efa-90f6-4f38-a17e-4d8a2be32c35/backend.log"
    # Ensure directory exists before using it
    if os.path.exists(os.path.dirname(local_path)):
        log_path = local_path
else:
    # Write outside apps/backend on Linux to prevent uvicorn reload infinite loop
    log_path = "../backend.log"


file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings


from app.db.database import Base, engine

# IMPORTANT - Register all models
import app.db.base

from fastapi.middleware.cors import CORSMiddleware
from app.security.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="The core API service powering the Nexora AI platform.",
)

# Mount static files for matplotlib plots and reports downloads
storage_reports_dir = os.path.join("storage", "reports")
os.makedirs(storage_reports_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=storage_reports_dir), name="reports")

# Register slowapi state and rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS Middleware to allow cross-origin requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



print("====================================")
print(Base.metadata.tables)
print("====================================")

Base.metadata.create_all(bind=engine)


app.include_router(api_router)




@app.on_event("startup")
def startup_event():
    # Enforce Environment Variables validation on startup
    if not settings.DATABASE_URL or ("postgresql" not in settings.DATABASE_URL and "sqlite" not in settings.DATABASE_URL):
        print("[CRITICAL] DATABASE_URL env variable is missing or invalid. Halting startup.")
        raise SystemExit(1)

        
    if not settings.SECRET_KEY or settings.SECRET_KEY == "CHANGE_THIS_LATER_IN_ENV":
        print("[CRITICAL] SECRET_KEY env variable is not configured for production. Halting startup.")
        raise SystemExit(1)

    print("[System] Startup environment validations successfully checked.")

    # Ensure database schema is initialized via SQLAlchemy Metadata
    try:
        Base.metadata.create_all(bind=engine)
        print("[System] Database tables verified successfully.")
    except Exception as e:
        print(f"[WARNING] Database schema verification: {e}")

    if settings.AI_PROVIDER.lower().strip() == "nexora":
        print(">>> NEXORA AI PROVIDER IS ACTIVE — Eagerly preloading model on startup <<<")
        try:
            from app.providers.nexora_provider import NexoraProvider
            NexoraProvider.preload_model()
            print(">>> Nexora model preloaded successfully <<<")
        except Exception as e:
            print(f"[WARNING] Nexora model preload failed on startup: {e}. Will retry on first chat request.")



@app.get("/metrics", tags=["General"])
def metrics():
    """
    Exposes standard Prometheus-formatted metrics gathered from MetricsService logs.
    Allows easy integration with Prometheus/Grafana monitoring agents.
    """
    if not settings.ENABLE_PROMETHEUS:
        return "Prometheus metrics disabled"
    
    from app.services.agents.metrics_service import MetricsService
    from fastapi.responses import PlainTextResponse
    
    try:
        data = MetricsService.get_dashboard_data()
        total_sess = data.get("total_sessions", 0)
        avg_lat = data.get("avg_latency_ms", 0)
        cost = data.get("total_cost_usd", 0.0)
        tokens_in = data.get("total_tokens_in", 0)
        tokens_out = data.get("total_tokens_out", 0)
        success_rate = data.get("success_rate", 0.0)

        lines = [
            "# HELP nexora_agent_sessions_total Total agent sessions executed",
            "# TYPE nexora_agent_sessions_total counter",
            f"nexora_agent_sessions_total {total_sess}",
            
            "# HELP nexora_agent_sessions_avg_latency_ms Average agent pipeline latency in milliseconds",
            "# TYPE nexora_agent_sessions_avg_latency_ms gauge",
            f"nexora_agent_sessions_avg_latency_ms {avg_lat}",
            
            "# HELP nexora_agent_sessions_cost_usd Cumulative API billing cost in USD",
            "# TYPE nexora_agent_sessions_cost_usd counter",
            f"nexora_agent_sessions_cost_usd {cost:.6f}",

            "# HELP nexora_agent_sessions_tokens_in_total Total prompt tokens processed",
            "# TYPE nexora_agent_sessions_tokens_in_total counter",
            f"nexora_agent_sessions_tokens_in_total {tokens_in}",

            "# HELP nexora_agent_sessions_tokens_out_total Total completion tokens generated",
            "# TYPE nexora_agent_sessions_tokens_out_total counter",
            f"nexora_agent_sessions_tokens_out_total {tokens_out}",

            "# HELP nexora_agent_sessions_success_rate Percentage of sessions completed successfully",
            "# TYPE nexora_agent_sessions_success_rate gauge",
            f"nexora_agent_sessions_success_rate {success_rate}"
        ]
        
        # Add per-agent specific metrics
        for name, agent in data.get("agents", {}).items():
            run_count = agent.get("runs", 0)
            agent_lat = agent.get("avg_latency_ms", 0)
            agent_cost = agent.get("total_cost_usd", 0.0)
            
            lines.extend([
                f'nexora_agent_runs_total{{agent="{name}"}} {run_count}',
                f'nexora_agent_latency_ms{{agent="{name}"}} {agent_lat}',
                f'nexora_agent_cost_usd{{agent="{name}"}} {agent_cost:.6f}'
            ])
            
        return PlainTextResponse("\n".join(lines) + "\n")
    except Exception as e:
        return PlainTextResponse(f"# Error gathering metrics: {e}\n", status_code=500)


@app.get("/", tags=["General"])
def root():
    return {"message": f"Welcome to {settings.APP_NAME} 🚀"}

