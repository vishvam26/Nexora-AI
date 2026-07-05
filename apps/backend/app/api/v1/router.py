from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.messages import router as messages_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.workspaces import router as workspaces_router
from app.api.v1.endpoints.folders import router as folders_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.workspace_members import router as workspace_members_router
from app.api.v1.endpoints.workspace_invitations import router as workspace_invitations_router
from app.api.v1.endpoints.shared_conversations import router as shared_conversations_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.comments import router as comments_router
from app.api.v1.endpoints.reactions import router as reactions_router
from app.api.v1.endpoints.favorites import router as favorites_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.workspace_templates import router as workspace_templates_router
from app.api.v1.endpoints.workspace_exports import router as workspace_exports_router
from app.api.v1.endpoints.workspace_imports import router as workspace_imports_router
from app.api.v1.endpoints.knowledge import router as knowledge_router
from app.api.v1.endpoints.advanced_search import router as advanced_search_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.rag_debug import router as rag_debug_router
from app.api.v1.endpoints.feedback import router as feedback_router
from app.api.v1.endpoints.quality import router as quality_router
from app.api.v1.endpoints.benchmark import router as benchmark_router
from app.api.v1.endpoints.cost import router as cost_router
from app.api.v1.endpoints.replay import router as replay_router
from app.api.v1.endpoints.monitoring import router as monitoring_router
from app.api.v1.endpoints.dataset_projects import router as dataset_projects_router
from app.api.v1.endpoints.training_projects import router as training_projects_router
from app.api.v1.endpoints.ml import router as ml_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(conversations_router)
api_router.include_router(messages_router)
api_router.include_router(chat_router)
api_router.include_router(workspaces_router)
api_router.include_router(folders_router)
api_router.include_router(search_router)
api_router.include_router(workspace_members_router)
api_router.include_router(workspace_invitations_router)
api_router.include_router(shared_conversations_router)
api_router.include_router(notifications_router)
api_router.include_router(comments_router)
api_router.include_router(reactions_router)
api_router.include_router(favorites_router)
api_router.include_router(dashboard_router)
api_router.include_router(workspace_templates_router)
api_router.include_router(workspace_exports_router)
api_router.include_router(workspace_imports_router)
api_router.include_router(knowledge_router)
api_router.include_router(advanced_search_router)
api_router.include_router(analytics_router)
api_router.include_router(ml_router)
api_router.include_router(rag_debug_router)
api_router.include_router(feedback_router)
api_router.include_router(quality_router)
api_router.include_router(benchmark_router)
api_router.include_router(cost_router)
api_router.include_router(replay_router)
api_router.include_router(monitoring_router)
api_router.include_router(dataset_projects_router)
api_router.include_router(training_projects_router)








