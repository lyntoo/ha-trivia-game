"""Select platform for Trivia Game."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, DIFFICULTIES, DEFAULT_DIFFICULTY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trivia select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create player device selects (1 to 4)
    player_selects = [
        TriviaPlayerDeviceSelect(coordinator, entry, hass, player_num)
        for player_num in range(1, 5)
    ]

    async_add_entities(
        [
            TriviaQuestionFileSelect(coordinator, entry),
            TriviaDifficultySelect(coordinator, entry),
        ] + player_selects
    )


class TriviaQuestionFileSelect(SelectEntity):
    """Representation of a Select entity for choosing a trivia question file."""

    _attr_icon = "mdi:file-question"

    def __init__(self, coordinator, entry: ConfigEntry):
        """Initialize the select entity."""
        self._coordinator = coordinator
        self._attr_name = "Fichier de questions Trivia"
        self._attr_unique_id = f"{entry.entry_id}_question_file"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
            manufacturer="Custom",
            model="Trivia Game",
        )
        # Initialize options list first to avoid AttributeError
        self._attr_options = []
        try:
            self._update_options()
        except Exception as e:
            _LOGGER.error(f"Error loading question files: {e}")
            self._attr_options = []

        # Set initial value from coordinator if available, else first option
        if self._attr_options and self._coordinator.question_file not in self._attr_options:
            self._coordinator.question_file = self._attr_options[0]
        elif not self._attr_options:
            _LOGGER.warning("No question files found!")
            self._coordinator.question_file = None


    def _get_files(self) -> list[str]:
        """Get list of question files."""
        path = self._coordinator.questions_path
        if not path or not path.exists():
            _LOGGER.warning(f"Questions path not found: {path}")
            return []
        files = sorted([f.name for f in path.glob("*.json")])
        _LOGGER.debug(f"Found question files: {files}")
        return files

    def _update_options(self):
        """Update the available options."""
        self._attr_options = self._get_files()

    @property
    def current_option(self) -> str | None:
        """Return the selected entity."""
        return self._coordinator.question_file

    @property
    def options(self) -> list[str]:
        """Return the available options."""
        return self._attr_options

    async def async_select_option(self, option: str) -> None:
        """Select the option."""
        await self._coordinator.async_set_question_file(option)

    async def async_update(self) -> None:
        """Update the entity."""
        self._update_options()
        if self._coordinator.question_file not in self._attr_options:
            new_option = self._attr_options[0] if self._attr_options else None
            await self._coordinator.async_set_question_file(new_option)


class TriviaDifficultySelect(SelectEntity):
    """Representation of a Select entity for choosing the game difficulty."""

    _attr_options = DIFFICULTIES
    _attr_icon = "mdi:podium"

    def __init__(self, coordinator, entry: ConfigEntry):
        """Initialize the select entity."""
        self._coordinator = coordinator
        self._attr_name = "Trivia Difficulté"
        self._attr_unique_id = f"{entry.entry_id}_difficulty"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )
        # Set initial value
        if self._coordinator.difficulty is None:
            self._coordinator.difficulty = DEFAULT_DIFFICULTY

    @property
    def current_option(self) -> str | None:
        """Return the selected entity."""
        return self._coordinator.difficulty

    async def async_select_option(self, option: str) -> None:
        """Select the option."""
        await self._coordinator.async_set_difficulty(option)


class TriviaPlayerDeviceSelect(SelectEntity):
    """Representation of a Select entity for choosing a player's mobile device."""

    _attr_icon = "mdi:cellphone"

    def __init__(self, coordinator, entry: ConfigEntry, hass: HomeAssistant, player_num: int):
        """Initialize the select entity."""
        self._coordinator = coordinator
        self._hass = hass
        self._player_num = player_num
        self._attr_name = f"Trivia Joueur {player_num}"
        self._attr_unique_id = f"{entry.entry_id}_player{player_num}_device"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Trivia Game",
        )
        # Initialize options list and device mapping
        self._attr_options = [""]
        self._device_map = {}  # {device_name: device_id}
        try:
            self._update_options()
        except Exception as e:
            _LOGGER.error(f"Error loading mobile devices for player {player_num}: {e}")
            self._attr_options = [""]
            self._device_map = {}

    def _get_mobile_devices(self) -> list[str]:
        """Get list of all mobile_app devices with their friendly names."""
        dev_reg = dr.async_get(self._hass)
        devices = []
        self._device_map = {}  # Reset mapping

        for device in dev_reg.devices.values():
            # Check if device belongs to mobile_app integration
            # device.config_entries is a set of config entry IDs (strings)
            has_mobile_app = False
            for entry_id in device.config_entries:
                # Access config entry from hass.config_entries
                config_entry = self._hass.config_entries.async_get_entry(entry_id)
                if config_entry and config_entry.domain == "mobile_app":
                    has_mobile_app = True
                    break

            if has_mobile_app:
                # Use device name or ID
                device_name = device.name or device.id
                # Store mapping device_name -> device_id
                self._device_map[device_name] = device.id
                # Add only the device name to the list
                devices.append(device_name)

        _LOGGER.debug(f"Found {len(devices)} mobile_app devices")
        return sorted(devices)

    def _update_options(self):
        """Update the available options."""
        devices = self._get_mobile_devices()
        # Add "Non sélectionné" option at the beginning
        self._attr_options = [""] + devices

    @property
    def current_option(self) -> str | None:
        """Return the selected device."""
        device_id = self._coordinator.selected_devices[self._player_num - 1]
        if not device_id:
            return ""

        # Find the device name from the device_id using the mapping
        for device_name, mapped_id in self._device_map.items():
            if mapped_id == device_id:
                return device_name

        return ""

    @property
    def options(self) -> list[str]:
        """Return the available options."""
        return self._attr_options

    async def async_select_option(self, option: str) -> None:
        """Select the option."""
        if option == "":
            # User selected "Non sélectionné"
            await self._coordinator.async_set_player_device(self._player_num, None)
        else:
            # Lookup device ID from device name using the mapping
            device_id = self._device_map.get(option)
            if device_id:
                await self._coordinator.async_set_player_device(self._player_num, device_id)
            else:
                _LOGGER.error(f"Device ID not found for device name: {option}")

    async def async_update(self) -> None:
        """Update the entity."""
        self._update_options()

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        # Only enable player 1 by default
        return self._player_num == 1