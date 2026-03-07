def supplier_to_blueprint(canonical):

    supplier_id = canonical["supplierId"]

    return {

        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": [

            {
                "property": "hasSupplierID",
                "value": supplier_id
            },

            {
                "property": "hasName",
                "value": canonical["supplierName"]
            },

            {
                "property": "hasCountry",
                "value": canonical["address"]["country"]
            }

        ],

        "objectProperties": []
    }
