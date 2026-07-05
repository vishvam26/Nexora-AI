# ==============================================================================
# Nexora AI Orchestration Automation Makefile
# ==============================================================================

.PHONY: up down restart logs build migrate shell clean status

# 1. Startup full stack containers
up:
	docker compose up -d

# 2. Shutdown containers and release networking layers
down:
	docker compose down

# 3. Quick restart of all services
restart:
	docker compose restart

# 4. Stream real-time container log files
logs:
	docker compose logs -f

# 5. Build or rebuild image layers without cache
build:
	docker compose build --no-cache

# 6. Run database migration schema upgrades via alembic
migrate:
	docker compose exec backend alembic upgrade head

# 7. Open terminal shell inside backend container
shell:
	docker compose exec backend sh

# 8. Clean up unused container networks and volume elements
clean:
	docker compose down -v
	docker system prune -f

# 9. Get status of running containers
status:
	docker compose ps
