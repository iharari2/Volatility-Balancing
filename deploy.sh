#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ec2-user/apps/Volatility-Balancing"
VENV_DIR="$APP_ROOT/venv"
SCRIPTS_DIR="$APP_ROOT/scripts"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

print_error() { echo -e "${RED}ERROR: $1${NC}" >&2; }
print_warning() { echo -e "${YELLOW}WARNING: $1${NC}"; }
print_success() { echo -e "${GREEN}$1${NC}"; }

usage() {
    cat << EOF
Usage: $0 [OPTIONS] [REF]

Deploy the Volatility-Balancing application.

Arguments:
  REF               Git ref to deploy (default: origin/main)

Options:
  --rollback        Rollback to previous version tag
  --skip-safety     Skip trading safety checks
  --tag-version     Create version tag after deployment
  -h, --help        Show this help message

Examples:
  $0                      # Deploy origin/main
  $0 v2025.01.27          # Deploy specific version
  $0 --rollback           # Rollback to previous version
  $0 --tag-version        # Deploy and create version tag

EOF
    exit 0
}

# Parse arguments
REF=""
ROLLBACK=false
SKIP_SAFETY=false
TAG_VERSION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --skip-safety)
            SKIP_SAFETY=true
            shift
            ;;
        --tag-version)
            TAG_VERSION=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            ;;
        *)
            REF="$1"
            shift
            ;;
    esac
done

# Set default REF
REF="${REF:-origin/main}"

cd "$APP_ROOT"

# Handle rollback
if [ "$ROLLBACK" = true ]; then
    echo "▶ Finding previous version tag..."

    # Get the two most recent version tags
    TAGS=$(git tag -l "v*" --sort=-creatordate | head -2)
    CURRENT_TAG=$(echo "$TAGS" | head -1)
    PREVIOUS_TAG=$(echo "$TAGS" | tail -1)

    if [ -z "$PREVIOUS_TAG" ] || [ "$PREVIOUS_TAG" = "$CURRENT_TAG" ]; then
        print_error "No previous version tag found for rollback"
        exit 1
    fi

    echo "  Current version:  $CURRENT_TAG"
    echo "  Rolling back to:  $PREVIOUS_TAG"
    REF="$PREVIOUS_TAG"
fi

# Trading safety check (unless skipped)
if [ "$SKIP_SAFETY" = false ]; then
    echo "▶ Running trading safety check..."

    if [ -f "$SCRIPTS_DIR/check_trading_safety.py" ]; then
        # Activate venv if it exists for the safety check
        if [ -d "$VENV_DIR" ]; then
            source "$VENV_DIR/bin/activate"
        fi

        if ! python3 "$SCRIPTS_DIR/check_trading_safety.py"; then
            print_warning "Trading safety check flagged potential issues."
            read -p "Continue with deployment? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Deployment cancelled."
                exit 1
            fi
        fi
    else
        print_warning "Trading safety script not found, skipping check."
    fi
fi

echo "▶ Deploying ref: $REF"

echo "▶ Fetching latest changes..."
git fetch origin --tags

echo "▶ Checking out $REF"
git checkout "$REF"

echo "▶ Ensuring virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "▶ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "▶ Restarting service..."
sudo systemctl restart volbalancing

echo "▶ Running smoke tests..."
./scripts/smoke.sh

# Create version tag if requested
if [ "$TAG_VERSION" = true ]; then
    echo "▶ Creating version tag..."

    TODAY=$(date +%Y.%m.%d)
    VERSION="v${TODAY}"

    # Check if tag exists, append suffix if needed
    EXISTING=$(git tag -l "${VERSION}*" | wc -l)
    if [ "$EXISTING" -gt 0 ]; then
        SUFFIX=$((EXISTING + 1))
        VERSION="${VERSION}.${SUFFIX}"
    fi

    git tag -a "$VERSION" -m "Release $VERSION"
    git push origin "$VERSION"

    print_success "Created and pushed tag: $VERSION"
fi

print_success "✅ Deploy completed successfully"

# Show current version info
if [ "$ROLLBACK" = true ]; then
    echo ""
    echo "Rollback complete. Deployed version: $REF"
    echo "To rollback further, run: $0 --rollback"
fi
