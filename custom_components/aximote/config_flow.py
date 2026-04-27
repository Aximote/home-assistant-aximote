"""Config flow for Aximote."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AximoteApiClient,
    AximoteApiError,
    AximoteAuthError,
    AximoteProRequiredError,
)
from .const import CONF_TOKEN, DEFAULT_BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AximoteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aximote."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Prompt for personal access token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = AximoteApiClient(
                session,
                DEFAULT_BASE_URL,
                user_input[CONF_TOKEN],
            )
            try:
                me = await client.async_me()
            except AximoteAuthError:
                errors["base"] = "invalid_auth"
            except AximoteProRequiredError:
                errors["base"] = "requires_pro"
            except AximoteApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Aximote connection")
                errors["base"] = "unknown"
            else:
                user_id = me.get("userId")
                if not user_id:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(str(user_id))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=str(me.get("email", user_id)),
                        data={CONF_TOKEN: user_input[CONF_TOKEN]},
                    )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TOKEN,
                    default=user_input.get(CONF_TOKEN, "") if user_input else "",
                ): str,
            },
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Re-authenticate when the PAT is revoked or invalid."""
        errors: dict[str, str] = {}
        reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"],
        )
        if reauth_entry is None:
            return self.async_abort(reason="unknown")

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = AximoteApiClient(
                session,
                DEFAULT_BASE_URL,
                user_input[CONF_TOKEN],
            )
            try:
                me = await client.async_me()
            except AximoteAuthError:
                errors["base"] = "invalid_auth"
            except AximoteProRequiredError:
                errors["base"] = "requires_pro"
            except AximoteApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Aximote reauth")
                errors["base"] = "unknown"
            else:
                user_id = str(me.get("userId", ""))
                if user_id != reauth_entry.unique_id:
                    return self.async_abort(reason="wrong_account")
                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data={CONF_TOKEN: user_input[CONF_TOKEN]},
                )
                await self.hass.config_entries.async_reload(reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN, default=""): str,
            },
        )
        return self.async_show_form(
            step_id="reauth",
            data_schema=schema,
            errors=errors,
        )
