@echo off
rem --- Mesa Platform, Copyright 2021 Vueocity, LLC

set PORT=9222
set ADT_PATH=c:\Tools\adt

rem -- Use this for chrome on android device
rem set DEVICE=localabstract:chrome_devtools_remote

rem -- Use this for kindlw
set DEVICE=localabstract:com.amazon.webapps.performancetester.devtools

echo ---------------------------------
echo  Starting Android debug server
echo  Use Chrome to look at localhost:%PORT% to debug connected Android device
echo  ADT must be installed at: %ADT_PATH%

echo %ADT_PATH%\sdk\platform-tools\adb forward tcp:%PORT% %DEVICE%
%ADT_PATH%\sdk\platform-tools\adb forward tcp:%PORT% %DEVICE%
