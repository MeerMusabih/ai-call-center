import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

log = open(os.path.join(BASE_DIR, "server.log"), "w", encoding="utf-8", buffering=1)
sys.stdout = log
sys.stderr = log

try:
    import uvicorn
    print("starting uvicorn")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
except Exception:
    import traceback
    traceback.print_exc(file=log)
