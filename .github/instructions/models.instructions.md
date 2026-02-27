# Models Instructions

Apply to: `src/netbox_data_puller/models/**/*.py`

## Rules

- Every model class inherits from `pydantic.BaseModel`
- Always set `model_config = ConfigDict(extra="allow")` so unknown
  API fields don't break deserialization
- Use `NestedRef` for related objects returned as `{id, display}`
- Use `ChoiceRef` for enum-like fields returned as `{value, label}`
- Field types must be explicit — no `Any` unless truly unavoidable
- Optional fields use `X | None = None` syntax (Python 3.13+)
- Each model file covers one NetBox resource type
- Export all public models from `models/__init__.py`
- Keep `extra="allow"` — never use `extra="forbid"` since the NetBox
  API may add new fields at any time

## Naming

- Model names match the NetBox resource: `Prefix`, `IPAddress`,
  `VLAN`, `VRF`
- File names are snake_case: `prefix.py`, `ip_address.py`, `vlan.py`

## Example Pattern

```python
from pydantic import BaseModel, ConfigDict

from .common import ChoiceRef, NestedRef


class ExampleResource(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    status: ChoiceRef
    tenant: NestedRef | None = None
    tags: list[NestedRef] = []
```
