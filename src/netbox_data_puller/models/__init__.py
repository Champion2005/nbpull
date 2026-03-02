"""📦 Pydantic models for NetBox IPAM, DCIM, and Tenancy resources."""

from netbox_data_puller.models.aggregate import Aggregate
from netbox_data_puller.models.common import ChoiceRef, NestedRef
from netbox_data_puller.models.device import Device
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.site import Site
from netbox_data_puller.models.tenant import Tenant
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF

__all__ = [
    "VLAN",
    "VRF",
    "Aggregate",
    "ChoiceRef",
    "Device",
    "IPAddress",
    "NestedRef",
    "Prefix",
    "Site",
    "Tenant",
]
