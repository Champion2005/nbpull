"""📦 Pydantic model for NetBox IPAM IP Address."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["IPAddress"]


class IPAddress(BaseModel):
    """NetBox IPAM IP Address resource."""

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    address: str
    status: ChoiceRef | None = None
    vrf: NestedRef | None = None
    tenant: NestedRef | None = None
    role: ChoiceRef | None = None
    assigned_object_type: str | None = None
    assigned_object_id: int | None = None
    dns_name: str = ""
    description: str = ""
    tags: list[NestedRef] = []
