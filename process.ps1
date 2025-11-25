# Change directory to gcp folder and run as module
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'e:\My Projects\major project\gcp'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start React frontend
cd knowell
npm run dev