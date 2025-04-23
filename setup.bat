@echo off
echo ===== Reading Project Setup =====
echo This script will install all necessary dependencies and set up the project environment
echo.

REM Check Python version
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install Python 3.12 or higher
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment
    exit /b 1
)
echo Virtual environment created successfully

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment
    exit /b 1
)
echo Virtual environment activated

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies
    exit /b 1
)
echo Dependencies installed successfully

REM Check OpenAI API key
echo.
if not exist .env (
    echo Creating .env file...
    echo OPENAI_API_KEY=your-api-key-here > .env
    echo .env file created. Please edit this file and add your OpenAI API key
) else (
    echo .env file already exists
)

echo.
echo ===== Installation Complete =====
echo To use the project, please ensure:
echo 1. You have set a valid OpenAI API key in the .env file
echo 2. Run the project using: python main.py your_book_file_path
echo.
echo Press any key to exit...
pause > nul
