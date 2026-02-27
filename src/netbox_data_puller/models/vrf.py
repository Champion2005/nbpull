"""📦 Pydantic model for NetBox IPAM VRF."""

from pydantic import BaseModel

from netbox_data_puller.models.prefix import NestedRef


class VRF(BaseModel, extra="allow"):
    """NetBox IPAM VRF resource."""

    id: int
    display: str
    name: str
    rd: str | None = None
    tenant: NestedRef | None = None
    enforce_unique: bool = True
    description: str = ""
    tags: list[NestedRef] = []
