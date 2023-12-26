@echo off
rem --- Mesa Platform, Copyright 2021 Vueocity, LLC

echo.
echo  Connecting to: %1
echo.

ssh -i .secrets/vueocity/%2.pem ec2-user@%1
