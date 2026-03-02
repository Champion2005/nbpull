"""📦 Pydantic model for NetBox DCIM Site."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["Site"]


class Site(BaseModel):
    """NetBox DCIM Site resource.

    Sites represent physical or logical locations (datacenters, offices,
    cloud regions) that group devices, racks, prefixes, and VLANs.
    """

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    name: str
    slug: str
    status: ChoiceRef | None = None
    region: NestedRef | None = None
    tenant: NestedRef | None = None
    facility: str = ""
    time_zone: str | None = None
    description: str = ""
    tags: list[NestedRef] = []
