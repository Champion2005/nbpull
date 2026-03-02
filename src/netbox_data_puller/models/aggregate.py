"""📦 Pydantic model for NetBox IPAM Aggregate."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import NestedRef

__all__ = ["Aggregate"]


class Aggregate(BaseModel):
    """NetBox IPAM Aggregate resource.

    Aggregates represent top-level IP space allocations from a RIR
    (Regional Internet Registry) or organisation.
    """

    model_config = ConfigDict(extra="allow")

    id: int
    display: str
    prefix: str
    rir: NestedRef | None = None
    tenant: NestedRef | None = None
    date_added: str | None = None
    description: str = ""
    tags: list[NestedRef] = []
