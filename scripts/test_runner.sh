#!/bin/bash
# Comprehensive test runner for lib2docScrape
# Usage: ./scripts/test_runner.sh [test_type] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
SKIP_SLOW=false
SKIP_REAL_WORLD=false
OUTPUT_DIR="reports"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [test_type] [options]

Test Types:
    unit            Run unit tests only
    integration     Run integration tests
    e2e             Run end-to-end tests
    performance     Run performance benchmarks
    all             Run all tests (default)

Options:
    --verbose       Enable verbose output
    --coverage      Generate coverage reports
    --skip-slow     Skip slow-running tests
    --skip-real     Skip real-world tests
    --output DIR    Output directory for reports (default: reports)
    --help          Show this help message

Examples:
    $0 unit --coverage
    $0 e2e --skip-slow
    $0 performance --verbose
    $0 all --coverage --output test_results
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        unit|integration|e2e|performance|all)
            TEST_TYPE="$1"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        --skip-real)
            SKIP_REAL_WORLD=true
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    print_warning "Virtual environment not found. Creating one..."
    uv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
uv pip install -e .
uv pip install pytest pytest-asyncio pytest-timeout pytest-html pytest-cov psutil

# Build pytest arguments
PYTEST_ARGS="-v"

if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -s"
fi

if [[ "$COVERAGE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term-missing --cov-report=html:$OUTPUT_DIR/htmlcov"
fi

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    local markers="not slow and not real_world and not performance"
    if [[ "$SKIP_SLOW" == "true" ]]; then
        markers="$markers and not slow"
    fi
    
    python -m pytest tests/ \
        -m "$markers" \
        --timeout=30 \
        --junit-xml="$OUTPUT_DIR/junit-unit.xml" \
        --html="$OUTPUT_DIR/unit-report.html" \
        $PYTEST_ARGS
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    local args="--timeout=60 --report=$OUTPUT_DIR/e2e-integration.json"
    
    if [[ "$SKIP_SLOW" == "true" ]]; then
        args="$args --skip-slow"
    fi
    
    if [[ "$SKIP_REAL_WORLD" == "true" ]]; then
        args="$args --skip-real-world"
    fi
    
    if [[ "$COVERAGE" == "true" ]]; then
        args="$args --coverage"
    fi
    
    python scripts/run_e2e_tests.py $args \
        --junit-xml="$OUTPUT_DIR/junit-integration.xml" \
        --html-report="$OUTPUT_DIR/integration-report.html"
}

# Function to run E2E tests
run_e2e_tests() {
    print_status "Running end-to-end tests..."
    
    local args="--timeout=90 --report=$OUTPUT_DIR/e2e-full.json"
    
    if [[ "$SKIP_SLOW" == "true" ]]; then
        args="$args --skip-slow"
    fi
    
    if [[ "$SKIP_REAL_WORLD" == "true" ]]; then
        args="$args --skip-real-world"
    fi
    
    python scripts/run_e2e_tests.py $args \
        --junit-xml="$OUTPUT_DIR/junit-e2e.xml" \
        --html-report="$OUTPUT_DIR/e2e-report.html"
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance benchmarks..."
    
    python scripts/run_e2e_tests.py \
        --performance-only \
        --timeout=120 \
        --report="$OUTPUT_DIR/performance-results.json" \
        --junit-xml="$OUTPUT_DIR/junit-performance.xml" \
        --html-report="$OUTPUT_DIR/performance-report.html"
}

# Function to check site availability
check_site_availability() {
    print_status "Checking test site availability..."
    
    python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from tests.e2e.test_sites import site_manager

async def check():
    availability = await site_manager.refresh_availability()
    available = sum(availability.values())
    total = len(availability)
    print(f'Sites available: {available}/{total}')
    
    for site_id, is_available in availability.items():
        status = '✓' if is_available else '✗'
        print(f'  {status} {site_id}')
    
    return available, total

available, total = asyncio.run(check())
exit(0 if available > 0 else 1)
"
    
    if [[ $? -ne 0 ]]; then
        print_warning "No test sites are available. Some tests may be skipped."
    fi
}

# Main execution
print_status "Starting lib2docScrape test runner..."
print_status "Test type: $TEST_TYPE"
print_status "Output directory: $OUTPUT_DIR"

# Check site availability for real-world tests
if [[ "$TEST_TYPE" == "all" || "$TEST_TYPE" == "integration" || "$TEST_TYPE" == "e2e" || "$TEST_TYPE" == "performance" ]]; then
    if [[ "$SKIP_REAL_WORLD" != "true" ]]; then
        check_site_availability
    fi
fi

# Run tests based on type
case $TEST_TYPE in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    performance)
        run_performance_tests
        ;;
    all)
        print_status "Running comprehensive test suite..."
        run_unit_tests
        run_integration_tests
        run_performance_tests
        ;;
    *)
        print_error "Unknown test type: $TEST_TYPE"
        show_usage
        exit 1
        ;;
esac

# Generate summary
print_success "Test execution completed!"
print_status "Reports generated in: $OUTPUT_DIR"

if [[ -f "$OUTPUT_DIR/htmlcov/index.html" ]]; then
    print_status "Coverage report: $OUTPUT_DIR/htmlcov/index.html"
fi

# List generated reports
print_status "Generated reports:"
find "$OUTPUT_DIR" -name "*.html" -o -name "*.xml" -o -name "*.json" | sort | while read -r file; do
    echo "  - $file"
done
