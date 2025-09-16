@echo off
REM Docker Test Runner Script for Noti Project (Windows)
REM This script provides various options for running tests in Docker containers

setlocal enabledelayedexpansion

REM Colors for output (Windows doesn't support colors in batch, so we'll use text)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Function to show help
:show_help
echo Docker Test Runner for Noti Project
echo.
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   test                    Run all tests
echo   test-unit              Run unit tests only
echo   test-api               Run API tests only
echo   test-integration       Run integration tests only
echo   test-models            Run model tests only
echo   test-coverage          Run tests with coverage report
echo   test-lint              Run linting checks
echo   test-all               Run all tests, coverage, and linting
echo   clean                  Clean up test containers and volumes
echo   logs                   Show test logs
echo   shell                  Open shell in test container
echo   help                   Show this help message
echo.
echo Options:
echo   --verbose              Verbose output
echo   --no-cache             Build without cache
echo   --parallel             Run tests in parallel
echo   --keep-db              Keep test database after tests
echo.
echo Examples:
echo   %0 test                # Run all tests
echo   %0 test-coverage       # Run tests with coverage
echo   %0 test-lint           # Run linting checks
echo   %0 clean               # Clean up test environment
goto :eof

REM Function to check if Docker is running
:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker is not running. Please start Docker and try again.
    exit /b 1
)
goto :eof

REM Function to build test image
:build_test_image
set "no_cache=%1"
echo %INFO% Building test image...

if "%no_cache%"=="true" (
    docker-compose -f docker-compose.test.yml build --no-cache test-runner
) else (
    docker-compose -f docker-compose.test.yml build test-runner
)

if errorlevel 1 (
    echo %ERROR% Failed to build test image
    exit /b 1
)

echo %SUCCESS% Test image built successfully
goto :eof

REM Function to run tests
:run_tests
set "test_type=%1"
set "verbose=%2"
set "parallel=%3"

echo %INFO% Starting test environment...

REM Start test services
docker-compose -f docker-compose.test.yml up -d test-db test-redis

REM Wait for services to be ready
echo %INFO% Waiting for test services to be ready...
timeout /t 10 /nobreak >nul

REM Build test image
call :build_test_image false

REM Prepare test command
set "test_command=python manage.py test"

if "%test_type%"=="unit" (
    set "test_command=python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models"
) else if "%test_type%"=="api" (
    set "test_command=python manage.py test apps.core.tests_api apps.notifications.tests_api apps.telegram_bot.tests_api"
) else if "%test_type%"=="integration" (
    set "test_command=python manage.py test apps.tests_integration"
) else if "%test_type%"=="models" (
    set "test_command=python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models"
) else if "%test_type%"=="all" (
    set "test_command=python manage.py test"
)

if "%verbose%"=="true" (
    set "test_command=!test_command! --verbosity=2"
)

if "%parallel%"=="true" (
    set "test_command=!test_command! --parallel"
)

REM Run tests
echo %INFO% Running tests: !test_command!
docker-compose -f docker-compose.test.yml run --rm test-runner !test_command!

if errorlevel 1 (
    echo %ERROR% Tests failed
    exit /b 1
)

echo %SUCCESS% Tests completed successfully
goto :eof

REM Function to run tests with coverage
:run_coverage
set "verbose=%1"

echo %INFO% Starting test environment with coverage...

REM Start test services
docker-compose -f docker-compose.test.yml up -d test-db test-redis

REM Wait for services to be ready
echo %INFO% Waiting for test services to be ready...
timeout /t 10 /nobreak >nul

REM Build test image
call :build_test_image false

REM Run tests with coverage
echo %INFO% Running tests with coverage...
docker-compose -f docker-compose.test.yml run --rm test-coverage

if errorlevel 1 (
    echo %ERROR% Coverage tests failed
    exit /b 1
)

echo %SUCCESS% Coverage report generated in htmlcov/
goto :eof

REM Function to run linting
:run_lint
echo %INFO% Running linting checks...

REM Build test image
call :build_test_image false

REM Run linting
docker-compose -f docker-compose.test.yml run --rm test-lint

if errorlevel 1 (
    echo %ERROR% Linting failed
    exit /b 1
)

echo %SUCCESS% Linting completed successfully
goto :eof

REM Function to clean up
:cleanup
echo %INFO% Cleaning up test environment...

REM Stop and remove containers
docker-compose -f docker-compose.test.yml down -v

REM Remove test images (ignore errors)
docker rmi noti_test_* 2>nul

REM Remove test volumes (ignore errors)
for /f "tokens=*" %%i in ('docker volume ls -q ^| findstr test') do docker volume rm %%i 2>nul

echo %SUCCESS% Test environment cleaned up
goto :eof

REM Function to show logs
:show_logs
echo %INFO% Showing test logs...
docker-compose -f docker-compose.test.yml logs test-runner
goto :eof

REM Function to open shell
:open_shell
echo %INFO% Opening shell in test container...

REM Start test services
docker-compose -f docker-compose.test.yml up -d test-db test-redis

REM Wait for services to be ready
echo %INFO% Waiting for test services to be ready...
timeout /t 10 /nobreak >nul

REM Build test image
call :build_test_image false

REM Open shell
docker-compose -f docker-compose.test.yml run --rm test-runner /bin/bash
goto :eof

REM Main script logic
:main
set "command=%1"
set "verbose=false"
set "no_cache=false"
set "parallel=false"
set "keep_db=false"

REM Parse arguments
shift
:parse_args
if "%~1"=="" goto :execute_command
if "%~1"=="--verbose" (
    set "verbose=true"
    shift
    goto :parse_args
)
if "%~1"=="--no-cache" (
    set "no_cache=true"
    shift
    goto :parse_args
)
if "%~1"=="--parallel" (
    set "parallel=true"
    shift
    goto :parse_args
)
if "%~1"=="--keep-db" (
    set "keep_db=true"
    shift
    goto :parse_args
)
echo %ERROR% Unknown option: %~1
call :show_help
exit /b 1

:execute_command
REM Check Docker
call :check_docker

REM Execute command
if "%command%"=="test" (
    call :run_tests "all" %verbose% %parallel%
) else if "%command%"=="test-unit" (
    call :run_tests "unit" %verbose% %parallel%
) else if "%command%"=="test-api" (
    call :run_tests "api" %verbose% %parallel%
) else if "%command%"=="test-integration" (
    call :run_tests "integration" %verbose% %parallel%
) else if "%command%"=="test-models" (
    call :run_tests "models" %verbose% %parallel%
) else if "%command%"=="test-coverage" (
    call :run_coverage %verbose%
) else if "%command%"=="test-lint" (
    call :run_lint
) else if "%command%"=="test-all" (
    call :run_lint
    call :run_coverage %verbose%
) else if "%command%"=="clean" (
    call :cleanup
) else if "%command%"=="logs" (
    call :show_logs
) else if "%command%"=="shell" (
    call :open_shell
) else if "%command%"=="help" (
    call :show_help
) else if "%command%"=="-h" (
    call :show_help
) else if "%command%"=="--help" (
    call :show_help
) else if "%command%"=="" (
    echo %ERROR% No command specified
    call :show_help
    exit /b 1
) else (
    echo %ERROR% Unknown command: %command%
    call :show_help
    exit /b 1
)

goto :eof

REM Run main function with all arguments
call :main %*
