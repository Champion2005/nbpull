"""📦 Pydantic model for NetBox IPAM Prefix."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["Prefix"]


class Prefix(BaseModel):
    """NetBox IPAM Prefix resource."""

    model_config = ConfigDict(extra="allow")

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
