#!/usr/bin/env bash
# OpenSpeakers — build and push all Docker images to Docker Hub.
#
# Usage:
#   ./scripts/docker-build-push.sh              # build + push all, version from VERSION file
#   ./scripts/docker-build-push.sh v0.2.0       # override version
#   ./scripts/docker-build-push.sh --push-only  # tag + push existing images (skip build)
#
# Prerequisites:
#   - docker login (must be logged into Docker Hub)
#   - All Dockerfiles must be buildable in the current tree
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

DOCKERHUB_USER="${DOCKERHUB_USERNAME:-davidamacey}"
PUSH_ONLY=false

# Parse args
VERSION=""
for arg in "$@"; do
  case "$arg" in
    --push-only) PUSH_ONLY=true ;;
    v*) VERSION="$arg" ;;
    *) VERSION="v$arg" ;;
  esac
done

# Read version from VERSION file if not provided
if [ -z "$VERSION" ]; then
  if [ -f VERSION ]; then
    VERSION="$(cat VERSION | tr -d '[:space:]')"
  else
    echo "ERROR: No version specified and no VERSION file found."
    echo "Usage: $0 [v0.1.0] [--push-only]"
    exit 1
  fi
fi

# Validate version format
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Invalid version format: $VERSION (expected vX.Y.Z)"
  exit 1
fi

echo "╔══════════════════════════════════════╗"
echo "║  OpenSpeakers Docker Build & Push    ║"
echo "║  Version: $VERSION                      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Docker login
if ! docker info 2>/dev/null | grep -qi "username"; then
  echo "ERROR: Not logged into Docker Hub. Run: docker login"
  exit 1
fi

# Image definitions: local_name:dockerfile:context
IMAGES=(
  "backend:backend/Dockerfile:backend"
  "frontend:frontend/Dockerfile.prod:frontend"
  "gpu-base:backend/Dockerfile.base-gpu:backend"
  "worker:backend/Dockerfile.worker:backend"
  "worker-fish:backend/Dockerfile.worker-fish:backend"
  "worker-qwen3:backend/Dockerfile.worker-qwen3:backend"
  "worker-orpheus:backend/Dockerfile.worker-orpheus:backend"
  "worker-dia:backend/Dockerfile.worker-dia:backend"
  "worker-f5:backend/Dockerfile.worker-f5:backend"
)

FAILED=()

for entry in "${IMAGES[@]}"; do
  IFS=: read -r name dockerfile context <<< "$entry"
  local_tag="open_speakers-${name}:latest"
  hub_latest="${DOCKERHUB_USER}/openspeakers-${name}:latest"
  hub_version="${DOCKERHUB_USER}/openspeakers-${name}:${VERSION}"

  echo ""
  echo "━━━ ${name} ━━━"

  # Build (unless --push-only)
  if [ "$PUSH_ONLY" = false ]; then
    echo "  Building ${local_tag} from ${dockerfile}..."
    if ! docker build -t "$local_tag" -f "$dockerfile" "$context"; then
      echo "  FAILED to build ${name}"
      FAILED+=("$name")
      continue
    fi
  fi

  # Tag
  echo "  Tagging -> ${hub_latest} and ${hub_version}"
  docker tag "$local_tag" "$hub_latest"
  docker tag "$local_tag" "$hub_version"

  # Push
  echo "  Pushing ${hub_latest}..."
  if ! docker push "$hub_latest"; then
    echo "  FAILED to push ${name}:latest"
    FAILED+=("$name")
    continue
  fi
  echo "  Pushing ${hub_version}..."
  if ! docker push "$hub_version"; then
    echo "  FAILED to push ${name}:${VERSION}"
    FAILED+=("$name")
    continue
  fi
  echo "  Done: ${name}"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "All ${#IMAGES[@]} images pushed successfully as :latest and :${VERSION}"
else
  echo "FAILED images: ${FAILED[*]}"
  exit 1
fi
