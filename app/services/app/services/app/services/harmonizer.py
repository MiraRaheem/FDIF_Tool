def harmonize_medwood_supplier(row):

    return {
        "supplierId": row.get("Cuenta de Cliente"),
        "supplierName": row.get("Razón Social"),
        "address": {
            "street": row.get("Calle"),
            "postalCode": row.get("Código Postal"),
            "city": row.get("Localidad"),
            "province": row.get("Provincia"),
            "autonomousCommunity": row.get("Comunidad Autónoma"),
            "country": row.get("País")
        }
    }
