"""Config flow for Trivia Game integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class TriviaConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Trivia Game."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            await self.async_set_unique_id("trivia_game_main")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title="Trivia Game", data={})

        return self.async_show_form(step_id="user")
