from app.services.budatech_v2.harmonizers import harmonize_customer

sample = {
    "ID": "BUD AeroTherm Forschung GmbH",
    "Customer Name": "BUD AeroTherm Forschung GmbH",
    "Customer Type": "Company",
}

canonical = harmonize_customer(sample)

assert canonical["customerId"] == "BUD AeroTherm Forschung GmbH"
assert canonical["customerName"] == "BUD AeroTherm Forschung GmbH"
assert canonical["customerType"] == "Company"

print(canonical)
