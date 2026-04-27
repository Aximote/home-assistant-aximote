"""DataUpdateCoordinator for Aximote."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AximoteApiClient,
    AximoteApiError,
    AximoteAuthError,
    AximoteProRequiredError,
    AximoteRateLimitedError,
)
from .const import AUX_POLL_INTERVAL_SEC, DOMAIN, SCAN_INTERVAL_SEC

_LOGGER = logging.getLogger(__name__)


@dataclass
class AximoteCoordinatorData:
    """Snapshot returned by the coordinator."""

    me: dict[str, Any]
    vehicles: list[dict[str, Any]]
    states: dict[str, dict[str, Any]]
    last_trips: dict[str, dict[str, Any] | None]
    last_refuels: dict[str, dict[str, Any] | None]


class AximoteDataUpdateCoordinator(DataUpdateCoordinator[AximoteCoordinatorData]):
    """Poll vehicles, live state, and periodically last trip/refuel."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: AximoteApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SEC),
        )
        self.client = client
        self._last_aux_monotonic: float = 0.0

    async def _async_update_data(self) -> AximoteCoordinatorData:
        try:
            vehicles = await self.client.async_list_vehicles()
            if not vehicles:
                _LOGGER.info(
                    "Aximote returned no vehicles for this account; "
                    "entities are created when at least one vehicle exists",
                )
            states_list = await asyncio.gather(
                *[
                    self.client.async_get_vehicle_state(v["id"])
                    for v in vehicles
                ],
            )
            states = {
                str(v["id"]): states_list[i]
                for i, v in enumerate(vehicles)
            }

            now_m = time.monotonic()
            prev = self.data
            if prev is None or (now_m - self._last_aux_monotonic) >= AUX_POLL_INTERVAL_SEC:
                self._last_aux_monotonic = now_m
                trip_pairs = await asyncio.gather(
                    *[
                        self.client.async_latest_trip(v["id"])
                        for v in vehicles
                    ],
                )
                refuel_pairs = await asyncio.gather(
                    *[
                        self.client.async_latest_refuel(v["id"])
                        for v in vehicles
                    ],
                )
                last_trips = {
                    str(v["id"]): trip_pairs[i]
                    for i, v in enumerate(vehicles)
                }
                last_refuels = {
                    str(v["id"]): refuel_pairs[i]
                    for i, v in enumerate(vehicles)
                }
            else:
                last_trips = dict(prev.last_trips)
                last_refuels = dict(prev.last_refuels)
                for v in vehicles:
                    vid = str(v["id"])
                    last_trips.setdefault(vid, prev.last_trips.get(vid))
                    last_refuels.setdefault(vid, prev.last_refuels.get(vid))

            me = await self.client.async_me()

            return AximoteCoordinatorData(
                me=me,
                vehicles=vehicles,
                states=states,
                last_trips=last_trips,
                last_refuels=last_refuels,
            )
        except AximoteAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except AximoteProRequiredError as err:
            raise ConfigEntryAuthFailed(f"Pro subscription required: {err}") from err
        except AximoteRateLimitedError as err:
            raise UpdateFailed(f"Rate limited: {err}") from err
        except AximoteApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed("Request timed out") from err
