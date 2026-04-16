from fastapi import FastAPI


from app.routers.frank import router as frank_router
from app.routers.budatec import router as budatec_router
from app.routers.medwood import router as medwood_router

app = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

# -------- ROUTERS --------
# Budatec
app.include_router(budatec_router, prefix="/fdif")

# Frank (already has /fdif/frank inside)
app.include_router(frank_router)

# Medwood (same logic as Budatec unless you added prefix inside it)
app.include_router(medwood_router, prefix="/fdif")

# -------- HEALTH --------
@app.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
