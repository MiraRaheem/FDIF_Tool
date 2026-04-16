from fastapi import FastAPI

from app.routers import medwood
from app.routers import budatec  
from app.routers.frank import router as frank_router

app.include_router(frank_router)

api = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

api.include_router(budatec, prefix="/fdif")
api.include_router(frank, prefix="/fdif")

@api.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
