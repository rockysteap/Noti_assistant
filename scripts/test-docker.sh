#!/bin/bash

# Docker Test Runner Script for Noti Project
# This script provides various options for running tests in Docker containers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to show help
show_help() {
    echo "Docker Test Runner for Noti Project"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  test                    Run all tests"
    echo "  test-unit              Run unit tests only"
    echo "  test-api               Run API tests only"
    echo "  test-integration       Run integration tests only"
    echo "  test-models            Run model tests only"
    echo "  test-coverage          Run tests with coverage report"
    echo "  test-lint              Run linting checks"
    echo "  test-all               Run all tests, coverage, and linting"
    echo "  clean                  Clean up test containers and volumes"
    echo "  logs                   Show test logs"
    echo "  shell                  Open shell in test container"
    echo "  help                   Show this help message"
    echo ""
    echo "Options:"
    echo "  --verbose              Verbose output"
    echo "  --no-cache             Build without cache"
    echo "  --parallel             Run tests in parallel"
    echo "  --keep-db              Keep test database after tests"
    echo ""
    echo "Examples:"
    echo "  $0 test                # Run all tests"
    echo "  $0 test-coverage       # Run tests with coverage"
    echo "  $0 test-lint           # Run linting checks"
    echo "  $0 clean               # Clean up test environment"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build test image
build_test_image() {
    local no_cache=$1
    print_status "Building test image..."
    
    local build_args=""
    if [ "$no_cache" = true ]; then
        build_args="--no-cache"
    fi
    
    docker-compose -f docker-compose.test.yml build $build_args test-runner
    print_success "Test image built successfully"
}

# Function to run tests
run_tests() {
    local test_type=$1
    local verbose=$2
    local parallel=$3
    
    print_status "Starting test environment..."
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d test-db test-redis
    
    # Wait for services to be ready
    print_status "Waiting for test services to be ready..."
    sleep 10
    
    # Build test image
    build_test_image false
    
    # Prepare test command
    local test_command="python manage.py test"
    
    case $test_type in
        "unit")
            test_command="python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models"
            ;;
        "api")
            test_command="python manage.py test apps.core.tests_api apps.notifications.tests_api apps.telegram_bot.tests_api"
            ;;
        "integration")
            test_command="python manage.py test apps.tests_integration"
            ;;
        "models")
            test_command="python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models"
            ;;
        "all")
            test_command="python manage.py test"
            ;;
    esac
    
    if [ "$verbose" = true ]; then
        test_command="$test_command --verbosity=2"
    fi
    
    if [ "$parallel" = true ]; then
        test_command="$test_command --parallel"
    fi
    
    # Run tests
    print_status "Running tests: $test_command"
    docker-compose -f docker-compose.test.yml run --rm test-runner $test_command
    
    print_success "Tests completed successfully"
}

# Function to run tests with coverage
run_coverage() {
    local verbose=$1
    
    print_status "Starting test environment with coverage..."
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d test-db test-redis
    
    # Wait for services to be ready
    print_status "Waiting for test services to be ready..."
    sleep 10
    
    # Build test image
    build_test_image false
    
    # Run tests with coverage
    print_status "Running tests with coverage..."
    docker-compose -f docker-compose.test.yml run --rm test-coverage
    
    print_success "Coverage report generated in htmlcov/"
}

# Function to run linting
run_lint() {
    print_status "Running linting checks..."
    
    # Build test image
    build_test_image false
    
    # Run linting
    docker-compose -f docker-compose.test.yml run --rm test-lint
    
    print_success "Linting completed successfully"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up test environment..."
    
    # Stop and remove containers
    docker-compose -f docker-compose.test.yml down -v
    
    # Remove test images
    docker rmi $(docker images -q noti_test_*) 2>/dev/null || true
    
    # Remove test volumes
    docker volume rm $(docker volume ls -q | grep test) 2>/dev/null || true
    
    print_success "Test environment cleaned up"
}

# Function to show logs
show_logs() {
    print_status "Showing test logs..."
    docker-compose -f docker-compose.test.yml logs test-runner
}

# Function to open shell
open_shell() {
    print_status "Opening shell in test container..."
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d test-db test-redis
    
    # Wait for services to be ready
    print_status "Waiting for test services to be ready..."
    sleep 10
    
    # Build test image
    build_test_image false
    
    # Open shell
    docker-compose -f docker-compose.test.yml run --rm test-runner /bin/bash
}

# Main script logic
main() {
    local command=$1
    local verbose=false
    local no_cache=false
    local parallel=false
    local keep_db=false
    
    # Parse arguments
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                verbose=true
                shift
                ;;
            --no-cache)
                no_cache=true
                shift
                ;;
            --parallel)
                parallel=true
                shift
                ;;
            --keep-db)
                keep_db=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check Docker
    check_docker
    
    # Execute command
    case $command in
        "test")
            run_tests "all" $verbose $parallel
            ;;
        "test-unit")
            run_tests "unit" $verbose $parallel
            ;;
        "test-api")
            run_tests "api" $verbose $parallel
            ;;
        "test-integration")
            run_tests "integration" $verbose $parallel
            ;;
        "test-models")
            run_tests "models" $verbose $parallel
            ;;
        "test-coverage")
            run_coverage $verbose
            ;;
        "test-lint")
            run_lint
            ;;
        "test-all")
            run_lint
            run_coverage $verbose
            ;;
        "clean")
            cleanup
            ;;
        "logs")
            show_logs
            ;;
        "shell")
            open_shell
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            print_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
