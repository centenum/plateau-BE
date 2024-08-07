import json
import random

test_units = [
    {"polling_unit": "SHILUR_MARKET",
  "ward": "SALUWE",
  "lga": "WASE"
}
,{"polling_unit": "ANG_MISSION_1",
  "ward": "GINDIRI 1",
  "lga": "MANGU"}

,{"polling_unit": "T_C_N_N",
  "ward": "DU",
  "lga": "JOS_SOUTH"}]

new_voters = []
with open('data/voters.json') as f:
    data = json.load(f)
    for i in data:
        random_polling_unit = random.choice(test_units)
        new_data = {**i, **random_polling_unit}
        new_voters.append(new_data)


with open('data/voters.json', 'w') as f:
    json.dump(new_voters, f)