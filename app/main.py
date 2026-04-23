from fastapi import FastAPI


from app.routers.budatec.supplier import router as supplier_router
from app.routers.budatec.customer import router as customer_router
from app.routers.medwood import router as medwood_router
from app.routers.cep_router import router as cep_router  # ✅ NEW
from app.routers.ontology_bootstrap import router as ontology_router
from app.routers.cep_data_router import router as cep_data_router
from app.routers.budatec.item import router as item_router



app = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

# -------- ROUTERS --------

# Budatec
app.include_router(supplier_router)
app.include_router(customer_router)
app.include_router(item_router)

# Medwood
app.include_router(medwood_router, prefix="/fdif")

# CEP (Melito + future real-time ingestion)
app.include_router(cep_router)  # ✅ NEW
app.include_router(cep_data_router)

app.include_router(ontology_router)

# -------- HEALTH --------
@app.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
