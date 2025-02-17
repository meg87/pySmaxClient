# pySmaxClient
SMAX client written in Python

How to Use:
------------
from smax_client import SMAXClient

smax = SMAXClient("https://smax.sample.com", "tenant_id", "username", "password")

entity_object = {
    "entity_type": "Request",
    "properties": {
        "DisplayLabel": "title",
        "Description": "description",
        "RequestedByPerson": "540499",
        "RequestedForPerson": "540499",
    }
}

response = smax.create_entity(entity_object)

print(response)
