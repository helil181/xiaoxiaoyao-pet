@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    小小耀桌宠 - PyInstaller 打包
echo ========================================
echo.

echo [1/2] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /q "*.spec" 2>nul
echo 清理完成

echo.
echo [2/2] 开始打包 (需要几分钟)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --noconsole ^
    --clean ^
    --optimize 2 ^
    --strip ^
    --noupx ^
    --name "小小耀桌宠" ^
    --add-data "sprites;sprites" ^
    --add-data "assets;assets" ^
    --add-data "messages.json;." ^
    --add-data "style_profile.json;." ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtNetwork ^
    --exclude-module tkinter ^
    --exclude-module unittest ^
    --exclude-module test ^
    --exclude-module jieba ^
    --exclude-module numpy ^
    --exclude-module matplotlib ^
    --exclude-module PIL ^
    --exclude-module pydoc ^
    --exclude-module xmlrpc ^
    --exclude-module distutils ^
    --exclude-module setuptools ^
    --exclude-module pip ^
    main.pyw

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 打包失败！请检查上面的错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✅ 打包成功！
echo    EXE 位置: dist\小小耀桌宠.exe
echo ========================================
echo.

for %%A in ("dist\小小耀桌宠.exe") do set "EXESIZE=%%~zA"
set /a EXESIZE_MB=%EXESIZE% / 1048576
echo 文件大小: %EXESIZE_MB% MB

echo.
pause
