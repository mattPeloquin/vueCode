@echo off
rem --- Mesa Platform, Copyright 2021 Vueocity, LLC

echo.
echo  Setting Path and virtual environment for MPF in:
echo    \%1
echo.

rem -- Prevent unicode errors from logging to console
set PYTHONIOENCODING=utf-8

rem -- Activate the virtual environment; this will put .venv\Scripts in path
call \%1\.venv\Scripts\activate.bat
