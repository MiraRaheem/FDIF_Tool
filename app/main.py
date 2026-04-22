from fastapi import FastAPI

from app.routers.frank import router as frank_router
from app.routers.budatec import router as budatec_router
from app.routers.medwood import router as medwood_router
from app.routers.cep_router import router as cep_router  # ✅ NEW
from app.routers.ontology_bootstrap import router as ontology_router


app = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

# -------- ROUTERS --------

# Budatec
app.include_router(budatec_router, prefix="/fdif")

# Frank (already has /fdif/frank inside)
app.include_router(frank_router)

# Medwood
app.include_router(medwood_router, prefix="/fdif")

# CEP (Melito + future real-time ingestion)
app.include_router(cep_router)  # ✅ NEW

app.include_router(ontology_router)
# -------- HEALTH --------
@app.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
