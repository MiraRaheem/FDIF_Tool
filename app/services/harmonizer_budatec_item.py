def harmonize_budatec_item(raw):

    return {
        "productId": raw.get("item_code"),
        "productName": raw.get("item_name"),
        "description": raw.get("description"),
        "category": raw.get("item_group"),

        "unit": raw.get("stock_uom"),
        "weight": raw.get("weight_per_unit"),

        "cost": raw.get("standard_rate"),
        "price": raw.get("valuation_rate"),

        "expiryDate": raw.get("end_of_life"),
        "bomId": raw.get("default_bom"),

        # 🔥 NEW
        "supplier": {
            "supplierId": raw.get("supplier"),
            "supplierPartNo": raw.get("supplier_part_no")
        },

        "customer": {
            "customerId": raw.get("customer"),
            "customerName": raw.get("customer_name")
        }
    }
