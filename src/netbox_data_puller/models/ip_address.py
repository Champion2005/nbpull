"""📦 Pydantic model for NetBox IPAM IP Address."""

from pydantic import BaseModel

from netbox_data_puller.models.prefix import ChoiceRef, NestedRef


class IPAddress(BaseModel, extra="allow"):
    """NetBox IPAM IP Address resource."""

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
