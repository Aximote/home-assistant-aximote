"""Base entity for Aximote."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AximoteDataUpdateCoordinator


class AximoteEntity(CoordinatorEntity[AximoteDataUpdateCoordinator]):
    """Base for Aximote entities tied to one vehicle."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AximoteDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.vehicle_id = vehicle_id
        vehicle_name = self._vehicle_name()
        model = self._vehicle_model()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vehicle_id)},
            name=vehicle_name,
            manufacturer="Aximote",
            model=model,
        )

    def _vehicle_dict(self) -> dict[str, Any] | None:
        for v in self.coordinator.data.vehicles:
            if str(v.get("id")) == self.vehicle_id:
                return v
        return None

    def _vehicle_name(self) -> str:
        v = self._vehicle_dict()
        if v and v.get("name"):
            return str(v["name"])
        return f"Vehicle {self.vehicle_id[:8]}"

    def _vehicle_model(self) -> str | None:
        v = self._vehicle_dict()
        if not v:
            return None
        parts = [v.get("make"), v.get("model")]
        joined = " ".join(str(p) for p in parts if p)
        return joined or None

    def _state_dict(self) -> dict[str, Any] | None:
        return self.coordinator.data.states.get(self.vehicle_id)
