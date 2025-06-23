@echo off
echo 🚀 Initializing Git Repository for AI Trip Planner
echo =====================================================

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed. Please install Git first.
    echo    Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Initialize git repository if not already initialized
if not exist .git (
    echo 📁 Initializing new Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Add all files (respecting .gitignore)
echo 📝 Adding files to Git...
git add .

REM Show status
echo 📊 Git Status:
git status --short

echo.
echo 🎉 Git repository ready!
echo.
echo 📋 Next steps:
echo 1. Review the files to be committed: git status
echo 2. Make your first commit: git commit -m "Initial commit: AI Trip Planner with Gemini"
echo 3. Create GitHub repository and add remote: git remote add origin [your-repo-url]
echo 4. Push to GitHub: git push -u origin main
echo.
echo 💡 Your test files and scripts are automatically ignored by .gitignore
echo.
pause
