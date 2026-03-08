from app.services.harmonizer import (
    harmonize_medwood_supplier,
    harmonize_supplier_performance
)

HARMONIZERS = {

    "supplierAccounts": harmonize_medwood_supplier,

    "supplierPerformance": harmonize_supplier_performance
}

def get_harmonizer(dataset):

    if dataset not in HARMONIZERS:
        raise Exception(f"No harmonizer registered for dataset: {dataset}")

    return HARMONIZERS[dataset]
