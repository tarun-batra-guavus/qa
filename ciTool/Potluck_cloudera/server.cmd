@echo off
set PATH=c:\Python27;%PATH%
set dir=%~dp0
@echo on
python.exe %dir%/src/ui_server.py %*
