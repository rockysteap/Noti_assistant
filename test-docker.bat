@echo off
REM Simple Docker Test Runner for Noti Project

echo [INFO] Starting Docker-based tests for Noti project...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Start test services
echo [INFO] Starting test database and Redis...
docker-compose -f docker-compose.test.yml up -d test-db test-redis

REM Wait for services to be ready
echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Run tests based on argument
if "%1"=="models" (
    echo [INFO] Running model tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models --verbosity=2
) else if "%1"=="api" (
    echo [INFO] Running API tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test apps.core.tests_api apps.notifications.tests_api apps.telegram_bot.tests_api --verbosity=2
) else if "%1"=="all" (
    echo [INFO] Running all tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test --verbosity=2
) else if "%1"=="core" (
    echo [INFO] Running core tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test apps.core --verbosity=2
) else if "%1"=="notifications" (
    echo [INFO] Running notification tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test apps.notifications --verbosity=2
) else if "%1"=="telegram" (
    echo [INFO] Running Telegram bot tests...
    docker-compose -f docker-compose.test.yml run --rm test-runner python manage.py test apps.telegram_bot --verbosity=2
) else if "%1"=="clean" (
    echo [INFO] Cleaning up test environment...
    docker-compose -f docker-compose.test.yml down -v
    echo [SUCCESS] Test environment cleaned up
) else (
    echo [INFO] Usage: test-docker.bat [models^|api^|all^|core^|notifications^|telegram^|clean]
    echo.
    echo Examples:
    echo   test-docker.bat models        # Run model tests
    echo   test-docker.bat api           # Run API tests  
    echo   test-docker.bat all           # Run all tests
    echo   test-docker.bat core          # Run core app tests
    echo   test-docker.bat clean         # Clean up test environment
)

echo.
echo [INFO] Test run completed!
