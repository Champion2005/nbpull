"""📦 Shared Pydantic types for NetBox API references."""

from pydantic import BaseModel, ConfigDict


class NestedRef(BaseModel):
    """Nested reference to a related object (id + display name).

    Used for related objects returned as ``{"id": 1, "display": "Foo"}``.
    """

    model_config = ConfigDict(extra="allow")

    id: int
    display: str


class ChoiceRef(BaseModel):
    """NetBox v4 choice/enum field (value + label).

    Used for status, role, and other enumerated fields that
    return ``{"value": "active", "label": "Active"}`` instead of
    ``{"id": 1, "display": "Active"}``.
    """

    model_config = ConfigDict(extra="allow")

    value: str
    label: str

    @property
    def display(self) -> str:
        """Consistent interface with NestedRef."""
        return self.label
