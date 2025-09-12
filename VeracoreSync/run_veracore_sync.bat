@echo off
REM Veracore Sync Batch Runner
REM This batch file runs the Veracore sync process

REM Set the working directory to where your script is located
cd /d "C:\VeracoreSync"

REM Activate your Python environment if using virtual environment
REM call "C:\VeracoreSync\venv\Scripts\activate.bat"

REM Run the Python script
python "C:\VeracoreSync\veracore_sync_scheduled.py"

REM Log the completion
echo %date% %time% - Veracore sync process completed >> "C:\VeracoreSync\logs\batch_log.txt"

REM Keep window open for debugging (remove this line for production)
REM pause