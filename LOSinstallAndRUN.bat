@echo off
@echo off

REM Check if LOS5.5.py exists
if exist LOS5.5.py (
    echo LOS5.5.py already exists.
) else (
    echo Downloading LOS5.5.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/StevoKeano/mestastic-utils/main/LOS5.5.py' -OutFile 'LOS5.5.py'"
    if errorlevel 1 (
        echo Failed to download LOS5.5.py
        exit /b 1
    ) else (
        echo LOS5.5.py downloaded successfully.
    )
)
rename LOS5.5.py los5.5.py
REM Check if myenv directory exists
if exist myenv (
    echo Virtual environment 'myenv' already exists. Activating...
    call myenv\Scripts\activate
) else (
    echo Creating new virtual environment 'myenv'...
    python -m venv myenv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
    echo Virtual environment created. Activating...
    call myenv\Scripts\activate
)

REM Check if activation was successful
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

echo Virtual environment is now active.

REM Install packages
for %%p in (numpy matplotlib cartopy pillow tqdm scipy pykdtree) do (
    pip install %%p
)

REM Install specific version of SRTM.py
pip install https://files.pythonhosted.org/packages/e6/07/1dc35011d5e68b6c873632fe07a517a1ad484bf4757ae4736320c4cab8ef/SRTM.py-0.3.7.tar.gz

echo All packages installed.
:app
@echo off
echo.
echo  _      ____   _____       ___    ____  ____  
echo ^| ^|    / __ \ / ____^|     / _ \  ^|  _ \^|  _ \ 
echo ^| ^|   ^| ^|  ^| ^| (___      / /_\ \ ^| ^|_) ^| ^|_) ^|
echo ^| ^|   ^| ^|  ^| ^|\___ \    / _____ \^|  ___/  __/ 
echo ^| ^|___^| ^|__^| ^|____) ^|  / /     \ \ ^|   ^| ^|   
echo ^|______\____/^|_____/  /_/       \_\_^|   ^|_^|  
echo.

REM Run your Python script
python los5.5.py

REM Keep the window open
goto :app