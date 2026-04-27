"""Sensors for Aximote."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import AximoteEntity


def _num(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_ts(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, str):
        return dt_util.parse_datetime(val)
    return val


class AximoteSensor(AximoteEntity, SensorEntity):
    """Sensor reading from coordinator snapshot."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator,
        unique_prefix: str,
        vehicle_id: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vehicle_id)
        self.entity_description = description
        self._attr_unique_id = f"{unique_prefix}_{vehicle_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        st = self._state_dict()
        v = self._vehicle_dict()
        trip = data.last_trips.get(self.vehicle_id)
        ref = data.last_refuels.get(self.vehicle_id)
        key = self.entity_description.key

        if key == "fuel_level_pct":
            return _num(st.get("fuelLevelPct")) if st else None
        if key == "battery_level_pct":
            return _num(st.get("batteryLevelPct")) if st else None
        if key == "range_km":
            return _num(st.get("rangeKm")) if st else None
        if key == "odometer_km":
            return _num(st.get("odometerKm")) if st else None
        if key == "speed_kmh":
            if not st:
                return None
            loc = st.get("location")
            if not isinstance(loc, dict):
                return None
            mps = _num(loc.get("speedMps"))
            return round(mps * 3.6, 3) if mps is not None else None
        if key == "bearing_deg":
            if not st:
                return None
            loc = st.get("location")
            if not isinstance(loc, dict):
                return None
            return _num(loc.get("bearingDeg"))
        if key == "captured_at":
            if not st:
                return None
            return _parse_ts(st.get("capturedAt"))
        if key == "current_trip_id":
            if not st:
                return None
            return st.get("currentTripId")

        if key == "make":
            return v.get("make") if v else None
        if key == "model":
            return v.get("model") if v else None
        if key == "year":
            y = v.get("year") if v else None
            return int(y) if y is not None else None
        if key == "fuel_type":
            if not v:
                return None
            ft = v.get("fuelType")
            if isinstance(ft, list):
                return ", ".join(str(x) for x in ft)
            return None
        if key == "fuel_capacity_l":
            return _num(v.get("fuelCapacityL")) if v else None
        if key == "battery_capacity_kwh":
            return _num(v.get("batteryCapacityKwh")) if v else None
        if key == "vehicle_updated_at":
            if not v:
                return None
            return _parse_ts(v.get("updatedAt"))

        if not isinstance(trip, dict):
            trip = {}
        if key == "last_trip_distance_km":
            return _num(trip.get("distanceKm"))
        if key == "last_trip_duration_sec":
            d = trip.get("durationSec")
            return int(d) if d is not None else None
        if key == "last_trip_avg_speed_kmh":
            return _num(trip.get("avgSpeedKmh"))
        if key == "last_trip_fuel_l":
            return _num(trip.get("fuelConsumedL"))
        if key == "last_trip_energy_kwh":
            return _num(trip.get("energyConsumedKwh"))
        if key == "last_trip_co2_kg":
            return _num(trip.get("co2Kg"))
        if key == "last_trip_eco_score":
            return _num(trip.get("ecoScore"))
        if key == "last_trip_speed_score":
            return _num(trip.get("speedScore"))
        if key == "last_trip_consistency_score":
            return _num(trip.get("consistencyScore"))
        if key == "last_trip_started_at":
            return _parse_ts(trip.get("startTime"))
        if key == "last_trip_ended_at":
            return _parse_ts(trip.get("endTime"))

        if not isinstance(ref, dict):
            ref = {}
        if key == "last_refuel_type":
            t = ref.get("type")
            return str(t).lower() if t is not None else None
        if key == "last_refuel_amount_l":
            return _num(ref.get("fuelAmountL"))
        if key == "last_refuel_energy_kwh":
            return _num(ref.get("energyChargedKwh"))
        if key == "last_refuel_avg_kw":
            return _num(ref.get("avgChargingKw"))
        if key == "last_refuel_cost":
            return _num(ref.get("costAmount"))
        if key == "last_refuel_started_at":
            return _parse_ts(ref.get("startTime"))
        if key == "last_refuel_ended_at":
            return _parse_ts(ref.get("endTime"))
        if key == "last_refuel_duration_sec":
            d = ref.get("durationSec")
            return int(d) if d is not None else None
        if key == "last_refuel_outside_temp_c":
            return _num(ref.get("outsideTemperature"))

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        key = self.entity_description.key
        if key != "last_refuel_cost":
            return {}
        ref = self.coordinator.data.last_refuels.get(self.vehicle_id)
        if not isinstance(ref, dict):
            return {}
        cur = ref.get("costCurrency")
        return {"cost_currency": cur} if cur is not None else {}


SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="fuel_level_pct",
        translation_key="fuel_level_pct",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="battery_level_pct",
        translation_key="battery_level_pct",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="range_km",
        translation_key="range_km",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="odometer_km",
        translation_key="odometer_km",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="speed_kmh",
        translation_key="speed_kmh",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="bearing_deg",
        translation_key="bearing_deg",
        native_unit_of_measurement="°",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="captured_at",
        translation_key="captured_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="current_trip_id",
        translation_key="current_trip_id",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="make",
        translation_key="vehicle_make",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="model",
        translation_key="vehicle_model",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="year",
        translation_key="vehicle_year",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="fuel_type",
        translation_key="fuel_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="fuel_capacity_l",
        translation_key="fuel_capacity_l",
        native_unit_of_measurement="L",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="battery_capacity_kwh",
        translation_key="battery_capacity_kwh",
        native_unit_of_measurement="kWh",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="vehicle_updated_at",
        translation_key="vehicle_updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_trip_distance_km",
        translation_key="last_trip_distance_km",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_trip_duration_sec",
        translation_key="last_trip_duration_sec",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="last_trip_avg_speed_kmh",
        translation_key="last_trip_avg_speed_kmh",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="last_trip_fuel_l",
        translation_key="last_trip_fuel_l",
        native_unit_of_measurement="L",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_trip_energy_kwh",
        translation_key="last_trip_energy_kwh",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="last_trip_co2_kg",
        translation_key="last_trip_co2_kg",
        native_unit_of_measurement="kg",
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="last_trip_eco_score",
        translation_key="last_trip_eco_score",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_trip_speed_score",
        translation_key="last_trip_speed_score",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_trip_consistency_score",
        translation_key="last_trip_consistency_score",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_trip_started_at",
        translation_key="last_trip_started_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="last_trip_ended_at",
        translation_key="last_trip_ended_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="last_refuel_type",
        translation_key="last_refuel_type",
    ),
    SensorEntityDescription(
        key="last_refuel_amount_l",
        translation_key="last_refuel_amount_l",
        native_unit_of_measurement="L",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_refuel_energy_kwh",
        translation_key="last_refuel_energy_kwh",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="last_refuel_avg_kw",
        translation_key="last_refuel_avg_kw",
        native_unit_of_measurement="kW",
        device_class=SensorDeviceClass.POWER,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_refuel_cost",
        translation_key="last_refuel_cost",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_refuel_started_at",
        translation_key="last_refuel_started_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="last_refuel_ended_at",
        translation_key="last_refuel_ended_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="last_refuel_duration_sec",
        translation_key="last_refuel_duration_sec",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="last_refuel_outside_temp_c",
        translation_key="last_refuel_outside_temp_c",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    added: set[str] = set()

    def _add_for_current_data() -> None:
        prefix = entry.unique_id or entry.entry_id
        new_entities: list[AximoteSensor] = []
        for vehicle in coordinator.data.vehicles:
            vid = str(vehicle["id"])
            for desc in SENSOR_DESCRIPTIONS:
                uid = f"{prefix}_{vid}_{desc.key}"
                if uid in added:
                    continue
                added.add(uid)
                new_entities.append(AximoteSensor(coordinator, prefix, vid, desc))
        if new_entities:
            async_add_entities(new_entities)

    _add_for_current_data()
    entry.async_on_unload(coordinator.async_add_listener(_add_for_current_data))
