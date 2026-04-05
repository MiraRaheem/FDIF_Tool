@router.post("/budatec/{entity_type}")
def ingest_budatec(entity_type: str, body: Dict[str, Any]):

    try:
        raw = body.get("data", {})

        if isinstance(raw, str):
            raw = json.loads(raw)

        # -----------------------------
        # SANITIZE ID EARLY
        # -----------------------------
        if raw.get("name"):
            raw["name"] = sanitize_id(raw["name"])

        # -----------------------------
        # SUPPLIER FLOW
        # -----------------------------
        if entity_type == "supplier":

            canonical = harmonize_budatec_supplier(raw)
            validated = validate_budatec_supplier(canonical)

            result = create_budatec_supplier(validated)

            return {
                "status": "success",
                "entity": "supplier",
                "canonical": canonical,
                "blueprint": result
            }

        # -----------------------------
        # CUSTOMER FLOW
        # -----------------------------
        elif entity_type == "customer":

            canonical = harmonize_budatec_customer(raw)
            validated = validate_budatec_customer(canonical)

            result = create_budatec_customer(validated)

            return {
                "status": "success",
                "entity": "customer",
                "canonical": canonical,
                "blueprint": result
            }

        # -----------------------------
        # UNKNOWN ENTITY
        # -----------------------------
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported entity_type: {entity_type}"
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
