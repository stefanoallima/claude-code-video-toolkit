@echo off
REM SUDD Command Sync Script (Windows)
REM Syncs commands from sudd/commands/ to CLI agent folders

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "SUDD_COMMANDS=%PROJECT_ROOT%\sudd\commands"

echo [sudd:sync] Syncing SUDD commands...

REM Sync to OpenCode CLI
set "TARGET=%PROJECT_ROOT%\.opencode\command"
if not exist "%TARGET%" mkdir "%TARGET%"

for %%f in ("%SUDD_COMMANDS%\macro\*.md") do (
    copy "%%f" "%TARGET%\sudd-%%~nf.md" >nul
    echo   [OK] opencode: sudd-%%~nf
)

for %%f in ("%SUDD_COMMANDS%\micro\*.md") do (
    copy "%%f" "%TARGET%\sudd-%%~nf.md" >nul
    echo   [OK] opencode: sudd-%%~nf
)

REM Sync to Claude Code CLI
set "TARGET=%PROJECT_ROOT%\.claude\commands\sudd"
if not exist "%TARGET%" mkdir "%TARGET%"

for %%f in ("%SUDD_COMMANDS%\macro\*.md") do (
    copy "%%f" "%TARGET%\%%~nf.md" >nul
    echo   [OK] claude: sudd/%%~nf
)

for %%f in ("%SUDD_COMMANDS%\micro\*.md") do (
    copy "%%f" "%TARGET%\%%~nf.md" >nul
    echo   [OK] claude: sudd/%%~nf
)

REM Sync to Crush CLI
set "TARGET=%PROJECT_ROOT%\.crush\commands"
if not exist "%TARGET%" mkdir "%TARGET%"

for %%f in ("%SUDD_COMMANDS%\macro\*.md") do (
    copy "%%f" "%TARGET%\sudd-%%~nf.md" >nul
    echo   [OK] crush: sudd-%%~nf
)

for %%f in ("%SUDD_COMMANDS%\micro\*.md") do (
    copy "%%f" "%TARGET%\sudd-%%~nf.md" >nul
    echo   [OK] crush: sudd-%%~nf
)

echo [sudd:sync] Done!
