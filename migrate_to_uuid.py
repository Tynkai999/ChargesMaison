import json
import uuid

with open("data.json", "r") as f:
    data = json.load(f)

# Maps to store old_id -> new_uuid for each model
id_maps = {
    "core.resident": {},
    "core.externalcontributor": {},
    "core.period": {},
    "core.chargetype": {},
    "core.charge": {},
    "core.presence": {},
    "core.wificontribution": {},
    "core.payment": {},
}

# First pass: assign UUIDs
for item in data:
    model = item["model"]
    if model in id_maps:
        old_id = item["pk"]
        new_id = str(uuid.uuid4())
        id_maps[model][old_id] = new_id
        item["pk"] = new_id

# Second pass: update FKs
for item in data:
    model = item["model"]
    fields = item["fields"]
    
    if model == "core.charge":
        fields["period"] = id_maps["core.period"].get(fields["period"], fields["period"])
        fields["charge_type"] = id_maps["core.chargetype"].get(fields["charge_type"], fields["charge_type"])
    elif model == "core.presence":
        fields["period"] = id_maps["core.period"].get(fields["period"], fields["period"])
        fields["resident"] = id_maps["core.resident"].get(fields["resident"], fields["resident"])
    elif model == "core.wificontribution":
        fields["period"] = id_maps["core.period"].get(fields["period"], fields["period"])
        fields["contributor"] = id_maps["core.externalcontributor"].get(fields["contributor"], fields["contributor"])
    elif model == "core.payment":
        fields["period"] = id_maps["core.period"].get(fields["period"], fields["period"])
        fields["resident"] = id_maps["core.resident"].get(fields["resident"], fields["resident"])

with open("data_uuid.json", "w") as f:
    json.dump(data, f, indent=4)
print("Migration of data.json to UUIDs complete.")
