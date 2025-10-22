@echo off
echo Installing...


REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    call python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
call pip install -r requirements.txt

echo.
echo Installation complete!

