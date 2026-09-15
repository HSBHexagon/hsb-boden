.PHONY: help build-web test-web check-web test-crm deploy-crm

help:
	@echo "HSB Hexagon Monorepo Commands:"
	@echo "  make build-web    - Builds Astro website for Cloudflare Pages"
	@echo "  make test-web     - Runs Vitest test suite for website"
	@echo "  make check-web    - Runs typecheck for website"
	@echo "  make test-crm     - Runs full Pytest suite for Sales OS CRM"
	@echo "  make deploy-crm   - Deploys Apps Script code to Google Sheet"

build-web:
	cd apps/website && npm run build

test-web:
	cd apps/website && npm run test:run

check-web:
	cd apps/website && npm run check

test-crm:
	cd apps/sales-os && PYTHONPATH=. pytest tests/test_drive_ecosystem_config.py tests/test_drive_ecosystem_scaffold.py -v

deploy-crm:
	cd apps/sales-os && ./deploy.sh
