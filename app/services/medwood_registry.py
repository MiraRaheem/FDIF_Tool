from app.services.harmonizer import harmonize_medwood_supplier


HARMONIZERS = {
    "supplierAccounts": harmonize_medwood_supplier
}


def get_harmonizer(dataset):

    if dataset not in HARMONIZERS:
        raise Exception(f"No harmonizer registered for dataset: {dataset}")

    return HARMONIZERS[dataset]
