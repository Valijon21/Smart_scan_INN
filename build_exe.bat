@echo off
echo INN TOp dasturini EXE formatiga o'tkazish boshlandi...

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller topilmadi. O'rnatilmoqda...
    pip install pyinstaller
)

echo.
echo Dastur yig'ilmoqda (Build)...
echo Iltimos, kuting...

REM Run PyInstaller
REM --windowed: No console window
REM --onedir: Create a folder (faster startup than --onefile)
REM --add-data: Include data.json and ocr.ps1
pyinstaller --noconfirm --onedir --windowed --name "INN_TOp" ^
    --add-data "data.json;." ^
    --add-data "app/ocr.ps1;app" ^
    main.py

echo.
echo ========================================================
echo JARAYON TUGADI!
echo.
echo Yangi dastur mana bu yerda:
echo dist\INN_TOp\INN_TOp.exe
echo.
echo Sheriklaringizga "dist\INN_TOp" papkasini to'liq ko'chirib berasiz.
echo ========================================================
pause
