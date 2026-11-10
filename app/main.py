from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.db.session import Base, engine
from app.api.routes import router
from app.models import models

app=FastAPI(title="Smart Waste Management & Recycling Operations System",version="1.0.0",description="Role-based waste collection, recycling, disposal and environmental analytics API")
Base.metadata.create_all(bind=engine)  # Convenient for local demo; use Alembic in deployed environments.
app.include_router(router)
@app.get('/health',tags=['System'])
def health(): return {"status":"ok","service":"smart-waste-management"}
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request:Request,exc:IntegrityError):
    return JSONResponse(status_code=409,content={"detail":"Database constraint conflict. Check duplicate values and referenced records."})
@app.exception_handler(Exception)
async def unexpected_error_handler(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"detail":"Internal server error"})
