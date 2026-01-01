"""Number platform for Trivia Game."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEFAULT_NUM_QUESTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trivia number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TriviaNumPlayersNumber(coordinator, entry),
            TriviaNumQuestionsNumber(coordinator, entry),
        ]
    )


class TriviaNumPlayersNumber(NumberEntity):
    """Representation of a 'Number of Players' number entity."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 4
    _attr_native_step = 1

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Nombre de joueurs"
        self._attr_unique_id = f"{entry.entry_id}_num_players"
        self._attr_icon = "mdi:account-multiple"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )

    @property
    def native_value(self) -> float | None:
        """Return the entity value."""
        return self._coordinator.num_players

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._coordinator.async_set_num_players(int(value))


class TriviaNumQuestionsNumber(NumberEntity):
    """Representation of a 'Number of Questions' number entity."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 50
    _attr_native_step = 1

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Nombre de questions"
        self._attr_unique_id = f"{entry.entry_id}_num_questions"
        self._attr_icon = "mdi:format-list-numbered"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )
        # Set initial value
        if self._coordinator.num_questions is None:
            self._coordinator.num_questions = DEFAULT_NUM_QUESTIONS


    @property
    def native_value(self) -> float | None:
        """Return the entity value."""
        return self._coordinator.num_questions

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._coordinator.async_set_num_questions(int(value))
