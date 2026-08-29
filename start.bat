@echo off
chcp 65001 >nul
title Zcode Conversation Cleaner
start "" pythonw "%~dp0main.py"
