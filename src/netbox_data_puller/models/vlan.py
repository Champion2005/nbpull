"""📦 Pydantic model for NetBox IPAM VLAN."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["VLAN"]


class VLAN(BaseModel):
    """NetBox IPAM VLAN resource."""

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    vid: int
    name: str
    status: ChoiceRef | None = None
    tenant: NestedRef | None = None
    site: NestedRef | None = None
    group: NestedRef | None = None
    role: NestedRef | None = None
    description: str = ""
    tags: list[NestedRef] = []
