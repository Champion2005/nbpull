"""📦 Pydantic model for NetBox IPAM Prefix."""

from pydantic import BaseModel


class NestedRef(BaseModel):
    """Nested reference to a related object (id + display name)."""

    id: int
    display: str


class ChoiceRef(BaseModel):
    """NetBox v4 choice/enum field (value + label).

    Used for status, role, and other enumerated fields that
    return {"value": "active", "label": "Active"} instead of
    {"id": 1, "display": "Active"}.
    """

    value: str
    label: str

    @property
    def display(self) -> str:
        """Consistent interface with NestedRef."""
        return self.label


class Prefix(BaseModel, extra="allow"):
    """NetBox IPAM Prefix resource."""

    id: int
    display: str
    prefix: str
    status: ChoiceRef | None = None
    vrf: NestedRef | None = None
    tenant: NestedRef | None = None
    site: NestedRef | None = None
    vlan: NestedRef | None = None
    role: NestedRef | None = None
    is_pool: bool = False
    mark_utilized: bool = False
    description: str = ""
    tags: list[NestedRef] = []
