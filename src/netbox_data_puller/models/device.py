"""📦 Pydantic model for NetBox DCIM Device."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["Device"]


class Device(BaseModel):
    """NetBox DCIM Device resource.

    Devices represent physical network hardware (routers, switches,
    servers) installed at a site, optionally mounted in a rack.
    """

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    name: str | None = None
    device_type: NestedRef | None = None
    role: NestedRef | None = None
    site: NestedRef | None = None
    rack: NestedRef | None = None
    status: ChoiceRef | None = None
    tenant: NestedRef | None = None
    platform: NestedRef | None = None
    primary_ip: NestedRef | None = None
    serial: str = ""
    description: str = ""
    tags: list[NestedRef] = []
