"""📦 Pydantic model for NetBox IPAM VLAN."""

from pydantic import BaseModel

from netbox_data_puller.models.prefix import ChoiceRef, NestedRef


class VLAN(BaseModel, extra="allow"):
    """NetBox IPAM VLAN resource."""

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
