"""Sensor platform for Trivia Game."""
import logging
from pathlib import Path

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trivia sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        TriviaGameStateSensor(coordinator, entry),
        TriviaCurrentQuestionSensor(coordinator, entry),
        TriviaQuestionFileSensor(coordinator, entry),
    ]

    # Add score sensors for each player
    for i in range(1, 5):
        sensors.append(TriviaPlayerScoreSensor(coordinator, entry, i))

    async_add_entities(sensors)


class TriviaGameStateSensor(SensorEntity):
    """Sensor for game state."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Game State"
        self._attr_unique_id = f"{entry.entry_id}_game_state"

    @property
    def state(self):
        """Return the state."""
        return "playing" if self._coordinator.game_active else "idle"

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "current_question_index": self._coordinator.current_question_index,
            "total_questions": len(self._coordinator.questions_pool),
            "num_players": len(self._coordinator.players),
        }


class TriviaCurrentQuestionSensor(SensorEntity):
    """Sensor for current question."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Current Question"
        self._attr_unique_id = f"{entry.entry_id}_current_question"

    @property
    def state(self):
        """Return the state."""
        if self._coordinator.current_question:
            return self._coordinator.current_question.get("question", "")
        return "No active question"

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if self._coordinator.current_question:
            return {
                "propositions": self._coordinator.current_question.get("propositions", []),
                "correct_answer": self._coordinator.current_question.get("réponse", ""),
                "anecdote": self._coordinator.current_question.get("anecdote", ""),
            }
        return {}


class TriviaPlayerScoreSensor(SensorEntity):
    """Sensor for player score."""

    def __init__(self, coordinator, entry, player_num):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._player_num = player_num
        self._attr_name = f"Trivia Player {player_num} Score"
        self._attr_unique_id = f"{entry.entry_id}_player{player_num}_score"

    @property
    def state(self):
        """Return the state."""
        return self._coordinator.scores.get(self._player_num, 0)

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        device = (
            self._coordinator.players[self._player_num - 1]
            if self._player_num <= len(self._coordinator.players)
            else None
        )
        return {
            "player_number": self._player_num,
            "device": device,
        }


class TriviaQuestionFileSensor(SensorEntity):
    """Sensor for available question files."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Question Files"
        self._attr_unique_id = f"{entry.entry_id}_question_files"

    @property
    def state(self):
        """Return the state."""
        return len(self._get_question_files())

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {"files": self._get_question_files()}

    def _get_question_files(self):
        """Get list of question files."""
        path = self._coordinator.questions_path
        if not path or not path.exists():
            return []
        return [f.name for f in path.glob("*.json")]