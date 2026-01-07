# fastapi/app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ROUTES
from app.api.routes import api_router

# -----------------------------------------------------
# Create app instance
# -----------------------------------------------------
app = FastAPI(title="DOS Device Assurance Console")

# -----------------------------------------------------
# Mount static files
# -----------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# -----------------------------------------------------
# Jinja2 template directory
# -----------------------------------------------------
templates = Jinja2Templates(directory="app/templates")

# -----------------------------------------------------
# Route Registration
# -----------------------------------------------------
app.include_router(api_router)

# -----------------------------------------------------
# Root Redirect -> /login
# -----------------------------------------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login")

# DEBUG: Show all routes
print("\n==== Registered Routes ====")
for route in app.routes:
    try:
        print(f"{route.path}  -->  {route.methods}")
    except AttributeError:
        # Static/Mount routes (no methods)
        print(f"{route.path}  -->  MOUNT")
print("===========================\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3399,
        reload=True
    )