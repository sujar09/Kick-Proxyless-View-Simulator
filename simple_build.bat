@echo off
echo StreamlinkTorGUI Build Script
echo ==============================

echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements
    pause
    exit /b 1
)

echo Building with PyInstaller...
pyinstaller streamlink_tor_gui.spec --clean --noconfirm
if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

echo Build completed successfully!
echo Executable is in the dist folder
pause