"""📦 Pydantic model for NetBox IPAM Prefix."""

from pydantic import BaseModel, ConfigDict

from netbox_data_puller.models.common import ChoiceRef, NestedRef

__all__ = ["Prefix"]


class Prefix(BaseModel):
    """NetBox IPAM Prefix resource.

    NetBox v4.2+ replaced the ``site`` foreign key with a generic
    ``scope`` relation (``scope_type`` / ``scope_id`` / ``scope``).
    Use :pyattr:`resolved_site` instead of accessing ``site`` directly
    — it checks ``scope`` first (when ``scope_type == "dcim.site"``)
    and falls back to the legacy ``site`` field for pre-v4.2 compat.
    """

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

    # NetBox v4.2+ scope fields (replace legacy ``site`` FK)
    scope_type: str | None = None
    scope_id: int | None = None
    scope: NestedRef | None = None

    @property
    def resolved_site(self) -> NestedRef | None:
        """Return the site reference, preferring ``scope`` over ``site``.

        * If ``scope_type`` is ``"dcim.site"`` → return ``scope``
        * Otherwise fall back to the legacy ``site`` field
        * Returns ``None`` when neither is set or scope points to a
          non-site object (e.g. ``dcim.location``, ``dcim.region``)
        """
        if self.scope is not None and self.scope_type == "dcim.site":
            return self.scope
        return self.site
