"""📦 Pydantic model for NetBox IPAM VRF."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import NestedRef

__all__ = ["VRF"]


class VRF(BaseModel):
    """NetBox IPAM VRF resource."""

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    name: str
    rd: str | None = None
    tenant: NestedRef | None = None
    enforce_unique: bool = True
    description: str = ""
    tags: list[NestedRef] = []
