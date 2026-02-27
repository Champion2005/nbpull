"""📦 Pydantic models for NetBox IPAM resources."""

from netbox_data_puller.models.common import ChoiceRef, NestedRef
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF

__all__ = [
    "VLAN",
    "VRF",
    "ChoiceRef",
    "IPAddress",
    "NestedRef",
    "Prefix",
]
