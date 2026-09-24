@echo off
title Full Throttle - Background Switcher
cd /d "%~dp0"
echo Full Throttle background switcher
echo F6 = Official remastered backgrounds
echo F7 = Custom remastered backgrounds
echo Keep this window open while playing.
echo.
tools\nutcracker-py312\Scripts\python.exe live_switcher.py
pause
