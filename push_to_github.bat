@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ======================================================
echo           TOOL PUSH CODE LEN GITHUB TU DONG
echo ======================================================
echo.

:: 1. Kiem tra Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] May cua ban chua cai dat Git hoac chua them vao PATH!
    echo Vui long cai Git tu https://git-scm.com/ truoc.
    pause
    exit /b 1
)

:: 2. Lay ten thu muc hien tai lam ten repo mac dinh
for %%I in (.) do set "folder_name=%%~nxI"

:: 3. Nhap thong tin commit
set /p msg="Nhap noi dung commit (Enter de mac dinh 'update code'): "
if "%msg%"=="" set msg=update code

:: 4. Kiem tra khoi tao Git Repo
if not exist ".git" (
    echo [*] Dang khoi tao Git repository...
    git init
    git branch -M main
)

:: 5. Kiem tra branch hien tai
for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set current_branch=%%a
if "%current_branch%"=="" set current_branch=main

:: 6. Stage & Commit
echo [*] Dang chuan bi file va commit...
git add .
git commit -m "%msg%"

:: 7. Kiem tra xem co GitHub CLI (gh) khong
where gh >nul 2>nul
if %errorlevel% equ 0 (
    :: Co GitHub CLI -> Kiem tra xem remote origin da co chua
    git remote get-url origin >nul 2>nul
    if !errorlevel! neq 0 (
        echo [*] Phat hien GitHub CLI. Dang kiem tra dang nhap...
        gh auth status >nul 2>nul
        if !errorlevel! equ 0 (
            echo [*] Dang tao repo tren GitHub thong qua GitHub CLI...
            gh repo create %folder_name% --private --source=. --remote=origin
        ) else (
            echo [!] GitHub CLI chua dang nhap. Vui long chay 'gh auth login' hoac nhap link repo ben duoi.
        )
    )
)

:: 8. Kiem tra xem da co remote 'origin' chua
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ------------------------------------------------------
    echo Chua tim thay remote 'origin' tren may cua ban!
    echo.
    echo Neu ban da tao Repository tren GitHub (vi du https://github.com/username/%folder_name%^),
    echo hay copy link HTTPS/SSH cua repo va dan vao day.
    echo ------------------------------------------------------
    set /p repo_url="Nhap GitHub Repository URL (VD: https://github.com/USER/REPO.git): "
    if "!repo_url!"=="" (
        echo [!] Khong co URL repo, khong the push!
        pause
        exit /b 1
    )
    git remote add origin !repo_url!
)

:: 9. Push code
echo.
echo [*] Dang day code len branch %current_branch%...
git push -u origin %current_branch%

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo  THANH CONG! Code da duoc day len GitHub.
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo  [!] CO LOI XAY RA KHI PUSH LEN GITHUB.
    echo  - Neu la repo moi co san file README/License, hay thu pull ve truoc.
    echo  - Kiem tra quyen truy cap / dang nhap GitHub cua ban.
    echo ======================================================
)

echo.
pause
