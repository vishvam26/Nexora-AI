from sqlalchemy.orm import Session
from app.repositories.search_repository import SearchRepository
from app.services.permission_service import PermissionService
from app.schemas.conversation import SearchResponse, SearchResult, MessageSearchMatch, ConversationResponse


class SearchService:
    """
    Service layer coordinating validations and global query searching across
    conversations and message logs.
    """

    @staticmethod
    def search(
        db: Session,
        user_id: int,
        workspace_id: int,
        query: str,
        folder_id: int = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        """
        Validates workspace search permission, performs ILIKE matching via SearchRepository,
        and constructs a paginated SearchResponse payload.
        """
        # Ensure user has search permission in this workspace
        PermissionService.check_permission(db, user_id, workspace_id, "search")

        # Execute search query
        results, total = SearchRepository.global_search(
            db, workspace_id, query, folder_id, limit, offset
        )

        # Serialize search results
        search_results = []
        for convo, matched_msgs in results:
            convo_res = ConversationResponse.model_validate(convo)
            msg_matches = [
                MessageSearchMatch.model_validate(msg) for msg in matched_msgs
            ]
            search_results.append(
                SearchResult(conversation=convo_res, matched_messages=msg_matches)
            )

        return SearchResponse(
            results=search_results,
            limit=limit,
            offset=offset,
            total=total
        )
