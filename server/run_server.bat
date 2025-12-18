@echo off
cd /d F:\AI-BI\server
F:\AI-BI\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
