@echo off
title Day Code Len GitHub De Deploy Web Online
color 0A
echo ===============================================================
echo   CONG CU HO TRO DAY WEB APP LEN GITHUB DE DEPLOY ONLINE
echo ===============================================================
echo.
echo Buoc 1: Vao trang https://github.com/new de tao 1 Repository moi.
echo (Dat ten vi du: grade3-practice-portal, de che do Public hoac Private tuy y)
echo.
set /p REPO_URL="Dan duong link Repository cua ban vao day (vi du: https://github.com/...): "

if "%REPO_URL%"=="" (
    echo Ban chua nhap link! Vui long chay lai file.
    pause
    exit /b
)

echo.
echo Dang ket noi va day code len GitHub...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main --force

echo.
echo ===============================================================
echo   THANH CONG! Code da duoc dua len GitHub.
echo.
echo Buoc tiep theo:
echo 1. Vao trang https://render.com dang nhap bang GitHub
echo 2. Chon New + -> Web Service -> Chon repo nay
echo 3. Bam Deploy -> Lay link https://...onrender.com gui cho hoc sinh!
echo ===============================================================
pause
