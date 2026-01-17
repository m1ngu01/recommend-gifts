@echo off
REM Start backend (Flask) and frontend (Vite) together

REM Update crawd subrepo before starting
IF EXIST "back\crawd\.git" (
    echo Updating crawd repository...
    pushd back\crawd
    git pull --ff-only
    popd
) ELSE (
    echo back\crawd not found or not a git repo. Skipping pull.
)

REM Backend
start "BACKEND" cmd /c "python back\app.py"

REM Frontend
start "FRONTEND" cmd /c "cd my-app && npm run dev"

echo Launched BACKEND (8000) and FRONTEND (3000).

