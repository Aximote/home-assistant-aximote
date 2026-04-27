"""Device tracker for Aximote vehicle location."""

from __future__ import annotations

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AximoteEntity


class AximoteDeviceTracker(AximoteEntity, TrackerEntity):
    """GPS location from public API vehicle state."""

    _attr_translation_key = "vehicle_location"

    def __init__(self, coordinator, unique_prefix: str, vehicle_id: str) -> None:
        super().__init__(coordinator, vehicle_id)
        self._attr_unique_id = f"{unique_prefix}_{vehicle_id}_location"
        self._apply_coordinator_data()

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False
        return self._attr_latitude is not None and self._attr_longitude is not None

    def _apply_coordinator_data(self) -> None:
        """Copy lat/lng from coordinator into TrackerEntity _attr_* (required by HA core)."""
        st = self._state_dict()
        lat: float | None = None
        lng: float | None = None
        acc = 0.0
        if st:
            loc = st.get("location")
            if isinstance(loc, dict):
                la = loc.get("latitude")
                lo = loc.get("longitude")
                if la is not None:
                    try:
                        lat = float(la)
                    except (TypeError, ValueError):
                        lat = None
                if lo is not None:
                    try:
                        lng = float(lo)
                    except (TypeError, ValueError):
                        lng = None
                ac = loc.get("accuracyM")
                if ac is not None:
                    try:
                        acc = float(ac)
                    except (TypeError, ValueError):
                        acc = 0.0
        self._attr_latitude = lat
        self._attr_longitude = lng
        self._attr_location_accuracy = acc

    async def async_added_to_hass(self) -> None:
        """Ensure attrs are set before the first state write (listener runs only after this)."""
        self._apply_coordinator_data()
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._apply_coordinator_data()
        super()._handle_coordinator_update()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device trackers."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    added: set[str] = set()

    def _add_for_current_data() -> None:
        prefix = entry.unique_id or entry.entry_id
        new_entities: list[AximoteDeviceTracker] = []
        for vehicle in coordinator.data.vehicles:
            vid = str(vehicle["id"])
            uid = f"{prefix}_{vid}_location"
            if uid in added:
                continue
            added.add(uid)
            new_entities.append(AximoteDeviceTracker(coordinator, prefix, vid))
        if new_entities:
            async_add_entities(new_entities)

    _add_for_current_data()
    entry.async_on_unload(coordinator.async_add_listener(_add_for_current_data))
