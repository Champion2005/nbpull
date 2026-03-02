"""📦 Pydantic model for NetBox Tenancy Tenant."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import NestedRef

__all__ = ["Tenant"]


class Tenant(BaseModel):
    """NetBox Tenancy Tenant resource.

    Tenants represent organisations or customers that own or use
    resources in NetBox. Used as a grouping/ownership dimension across
    IPAM, DCIM, and Virtualization resources.
    """

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    name: str
    slug: str
    group: NestedRef | None = None
    description: str = ""
    tags: list[NestedRef] = []
