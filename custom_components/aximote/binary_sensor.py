"""Binary sensors for Aximote."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AximoteEntity


class AximoteBinarySensor(AximoteEntity, BinarySensorEntity):
    """Binary sensor from vehicle state."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator,
        unique_prefix: str,
        vehicle_id: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vehicle_id)
        self.entity_description = description
        self._attr_unique_id = f"{unique_prefix}_{vehicle_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        st = self._state_dict()
        if st is None:
            return None
        if self.entity_description.key == "on_trip":
            val = st.get("onTrip")
        elif self.entity_description.key == "ignition_on":
            val = st.get("ignitionOn")
        else:
            return None
        if val is None:
            return None
        return bool(val)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = (
        BinarySensorEntityDescription(
            key="on_trip",
            translation_key="on_trip",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        BinarySensorEntityDescription(
            key="ignition_on",
            translation_key="ignition_on",
            device_class=BinarySensorDeviceClass.POWER,
        ),
    )
    added: set[str] = set()

    def _add_for_current_data() -> None:
        prefix = entry.unique_id or entry.entry_id
        new_entities: list[AximoteBinarySensor] = []
        for vehicle in coordinator.data.vehicles:
            vid = str(vehicle["id"])
            for desc in descriptions:
                uid = f"{prefix}_{vid}_{desc.key}"
                if uid in added:
                    continue
                added.add(uid)
                new_entities.append(
                    AximoteBinarySensor(coordinator, prefix, vid, desc),
                )
        if new_entities:
            async_add_entities(new_entities)

    _add_for_current_data()
    entry.async_on_unload(coordinator.async_add_listener(_add_for_current_data))
