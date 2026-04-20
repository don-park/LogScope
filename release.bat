@echo off
setlocal
echo =============================================
echo  LogScope Release Build
echo =============================================
echo.

:: conda 환경 이름
set ENV_NAME=test_env1

:: 프로젝트 루트로 이동 (스크립트 위치 기준)
cd /d "%~dp0"

echo [1/3] Running tests...
conda run -n %ENV_NAME% python -m unittest discover -s app/tests -q
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAILED] Tests failed. Build aborted.
    pause
    exit /b 1
)
echo        Tests passed.
echo.

echo [2/3] Building exe with PyInstaller...
conda run -n %ENV_NAME% python -m PyInstaller logscope.spec --noconfirm
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAILED] PyInstaller build failed.
    pause
    exit /b 1
)
echo.

echo [3/3] Build complete.
echo        Output: dist\LogScope.exe
for %%A in (dist\LogScope.exe) do echo        Size:   %%~zA bytes
echo.
echo =============================================
echo  Done.
echo =============================================
pause
