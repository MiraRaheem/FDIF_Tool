from fastapi import FastAPI

from app.routers import budatec
from app.routers.frank import router as frank_router

app = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

# -------- ROUTERS --------

# Budatec (module router)
app.include_router(budatec, prefix="/fdif")

# Frank (already has prefix inside)
app.include_router(frank_router)

# -------- HEALTH --------
@app.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
