"""Button platform for Trivia Game."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trivia button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TriviaStartGameButton(coordinator, entry),
            TriviaNextQuestionButton(coordinator, entry),
            TriviaStopGameButton(coordinator, entry),
        ]
    )


class TriviaStartGameButton(ButtonEntity):
    """Representation of a 'Start Game' button."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Démarrer le jeu"
        self._attr_unique_id = f"{entry.entry_id}_start_game_button"
        self._attr_icon = "mdi:play-circle"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._coordinator.start_game()


class TriviaNextQuestionButton(ButtonEntity):
    """Representation of a 'Next Question' button."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Question Suivante"
        self._attr_unique_id = f"{entry.entry_id}_next_question_button"
        self._attr_icon = "mdi:arrow-right-circle-outline"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._coordinator.next_question()


class TriviaStopGameButton(ButtonEntity):
    """Representation of a 'Stop Game' button."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Arrêter le jeu"
        self._attr_unique_id = f"{entry.entry_id}_stop_game_button"
        self._attr_icon = "mdi:stop-circle-outline"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._coordinator.stop_game()
