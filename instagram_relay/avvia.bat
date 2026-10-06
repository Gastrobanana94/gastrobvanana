@echo off
rem Accende il relay e il ponte ngrok (indirizzo fisso). Doppio clic per avviare.
cd /d "%~dp0"
start "RELAY Instagram" cmd /k python relay.py
start "PONTE ngrok" cmd /k ngrok http 8787 --url https://paying-cake-engulf.ngrok-free.dev
