@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Training ML models...
python manage.py train_ml_models %*

echo.
echo Done!
pause
