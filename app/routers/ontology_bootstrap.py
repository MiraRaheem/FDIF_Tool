from fastapi import APIRouter, HTTPException
from app.services.ontology_bootstrap import bootstrap_ontology

router = APIRouter(prefix="/fdif/ontology", tags=["Ontology Bootstrap"])


@router.post("/bootstrap")
def bootstrap():

    try:
        result = bootstrap_ontology()

        return {
            "status": "success",
            "details": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
