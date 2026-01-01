"""Trivia Game integration for Home Assistant."""
import asyncio
import logging
import json
import random
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_START_GAME,
    SERVICE_STOP_GAME,
    SERVICE_NEXT_QUESTION,
    SERVICE_CHECK_ANSWER,
    DEFAULT_DIFFICULTY,
    DEFAULT_NUM_QUESTIONS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "select", "button", "number"]


class MyStaticPathConfig:
    """A simple container for static path configuration."""

    def __init__(self, url_path, path, cache_headers):
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Trivia component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trivia from a config entry."""
    coordinator = TriviaGameCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass, entry)

    # Register event listener for notification actions
    async def handle_notification_action(event):
        """Handle mobile app notification action events."""
        action = event.data.get("action", "")

        # Check if this is a trivia answer action
        if action.startswith("TRIVIA_ANSWER_"):
            # Parse action: TRIVIA_ANSWER_A_1 -> answer=A, player=1
            parts = action.replace("TRIVIA_ANSWER_", "").split("_")
            if len(parts) == 2:
                answer_letter = parts[0]  # A, B, or C (3 choices only)
                player_num = int(parts[1])  # 1, 2, 3, 4

                _LOGGER.info(f"Player {player_num} answered: {answer_letter}")

                # Call check_answer with the answer letter
                await coordinator.check_answer(player_num, answer_letter)

    # Subscribe to mobile_app notification action events
    hass.bus.async_listen("mobile_app_notification_action", handle_notification_action)

    # Register frontend panel
    await hass.http.async_register_static_paths(
        [
            MyStaticPathConfig(
                url_path=f"/{DOMAIN}/panel",
                path=hass.config.path(f"custom_components/{DOMAIN}/www"),
                cache_headers=False,
            )
        ]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up services for Trivia integration."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async def start_game(call: ServiceCall) -> None:
        """Start a new trivia game."""
        await coordinator.start_game(
            players_devices=call.data.get("players_devices", {}),
        )

    async def stop_game(call: ServiceCall) -> None:
        """Stop the current game."""
        await coordinator.stop_game()

    async def next_question(call: ServiceCall) -> None:
        """Send the next question."""
        await coordinator.next_question()

    async def check_answer(call: ServiceCall) -> None:
        """Check a player's answer."""
        await coordinator.check_answer(
            player=call.data.get("player"),
            answer=call.data.get("answer"),
        )

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_GAME,
        start_game,
        schema=vol.Schema(
            {
                vol.Required("players_devices"): dict,
            }
        ),
    )

    hass.services.async_register(DOMAIN, SERVICE_STOP_GAME, stop_game)
    hass.services.async_register(DOMAIN, SERVICE_NEXT_QUESTION, next_question)
    hass.services.async_register(
        DOMAIN,
        SERVICE_CHECK_ANSWER,
        check_answer,
        schema=vol.Schema(
            {
                vol.Required("player"): cv.positive_int,
                vol.Required("answer"): cv.string,
            }
        ),
    )


class TriviaGameCoordinator(DataUpdateCoordinator):
    """Coordinator for managing trivia game state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.entry = entry
        self.questions_path = Path(__file__).parent / "questions"

        # Game state
        self.game_active = False
        self.questions_pool = []
        self.scores = {}
        self.players = []

        # État par joueur (chaque joueur a sa propre progression)
        self.player_question_index = {}  # {player_num: index}
        self.player_current_question = {}  # {player_num: question}
        self.player_finished = {}  # {player_num: bool} pour suivre qui a terminé

        # Game options
        self.num_players: int = 1
        self.num_questions: int = DEFAULT_NUM_QUESTIONS
        self.difficulty: str = DEFAULT_DIFFICULTY
        self.question_file: str | None = None

        # Selected player devices (4 joueurs max)
        self.selected_devices: list[str | None] = [None, None, None, None]

        # Mapping des propositions affichées pour chaque joueur (3 choix sur 4)
        # Format: {player_num: {"A": "proposition text", "B": "...", "C": "..."}}
        self.player_displayed_choices = {}

    @callback
    def _update_listeners(self):
        """Update listeners of state change."""
        self.async_update_listeners()

    async def async_set_num_players(self, value: int):
        self.num_players = value
        self._update_listeners()

    async def async_set_num_questions(self, value: int):
        self.num_questions = value
        self._update_listeners()

    async def async_set_difficulty(self, value: str):
        self.difficulty = value
        self._update_listeners()

    async def async_set_question_file(self, value: str | None):
        self.question_file = value
        self._update_listeners()

    async def async_set_player_device(self, player_num: int, device_id: str | None):
        """Set the device for a specific player (1-4)."""
        if 1 <= player_num <= 4:
            self.selected_devices[player_num - 1] = device_id
            _LOGGER.debug(f"Player {player_num} device set to: {device_id}")
            self._update_listeners()

    def get_selected_devices(self) -> list[str]:
        """Get only the devices for active players."""
        devices = [d for d in self.selected_devices[:self.num_players] if d]
        _LOGGER.debug(f"Selected devices for {self.num_players} players: {devices}")
        return devices

    async def _get_notify_service_for_device(self, device_id: str) -> str | None:
        """Find the notify service for a given mobile_app device ID."""
        from homeassistant.helpers import device_registry as dr

        dev_reg = dr.async_get(self.hass)
        device = dev_reg.async_get(device_id)

        if not device:
            _LOGGER.warning(f"Device not found: {device_id}")
            return None

        # For mobile_app, the notify service is: notify.mobile_app_<device_name>
        # The device name is sanitized (lowercase, spaces->underscores, special chars removed)
        device_name = device.name or device.id

        # Sanitize device name for service name
        import re
        sanitized_name = re.sub(r'[^a-z0-9_]', '_', device_name.lower())
        sanitized_name = re.sub(r'_+', '_', sanitized_name).strip('_')

        service_name = f"mobile_app_{sanitized_name}"

        _LOGGER.debug(f"Device '{device_name}' -> notify service: {service_name}")

        # Verify the service exists
        if not self.hass.services.has_service("notify", service_name):
            _LOGGER.warning(f"Notify service 'notify.{service_name}' not found for device '{device_name}'")
            return None

        return service_name

    async def start_game(self, players_devices: dict[str, Any] | None = None) -> None:
        """Start a new game, reading options from coordinator state."""
        if not self.question_file:
            _LOGGER.error("Cannot start game: no question file selected.")
            return

        # Get device IDs from parameter or from selected devices
        if players_devices:
            device_ids = players_devices.get("device_id", [])
        else:
            device_ids = self.get_selected_devices()

        if not device_ids:
            _LOGGER.error("Cannot start game: no player devices selected.")
            return

        _LOGGER.info(
            f"Starting game: {self.num_players} players, {self.question_file}, "
            f"{self.difficulty}, {self.num_questions} questions"
        )

        # Reset game state
        self.game_active = True
        self.players = device_ids[: self.num_players]
        self.scores = {i + 1: 0 for i in range(self.num_players)}
        self.player_displayed_choices = {}  # Reset choices mapping

        # Initialiser l'état par joueur
        self.player_question_index = {i + 1: 0 for i in range(self.num_players)}
        self.player_current_question = {}
        self.player_finished = {i + 1: False for i in range(self.num_players)}

        self._update_listeners()

        # Load questions
        await self._load_questions()

        # Send first question to each player independently
        for player_num in range(1, self.num_players + 1):
            await self.next_question(player_num)

    async def _load_questions(self) -> None:
        """Load questions from JSON file using coordinator state."""
        file_path = self.questions_path / self.question_file

        def load_json():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            questions = data["quizz"]["fr"][self.difficulty]
            return random.sample(questions, min(self.num_questions, len(questions)))

        self.questions_pool = await self.hass.async_add_executor_job(load_json)
        _LOGGER.info(f"Loaded {len(self.questions_pool)} questions")
        self._update_listeners()

    async def next_question(self, player_num: int) -> None:
        """Send the next question to a specific player."""
        if not self.game_active:
            _LOGGER.debug("Next question called but game is not active.")
            return

        # Vérifier si ce joueur a terminé
        player_index = self.player_question_index[player_num]
        if player_index >= len(self.questions_pool):
            # Ce joueur a terminé toutes ses questions
            self.player_finished[player_num] = True
            _LOGGER.info(f"Player {player_num} has finished all questions")

            # Vérifier si TOUS les joueurs ont terminé
            if all(self.player_finished.values()):
                _LOGGER.info("All players finished, stopping game")
                await self.stop_game()
            return

        # Récupérer la question pour ce joueur
        self.player_current_question[player_num] = self.questions_pool[player_index]
        self._update_listeners()

        # Envoyer la notification seulement à ce joueur
        device_id = self.players[player_num - 1]  # player_num est 1-indexed
        await self._send_question_notification(player_num, device_id)

    async def _send_question_notification(
        self, player_num: int, device_id: str
    ) -> None:
        """Send question notification to a player with 3 choices (Android limit)."""
        service_name = await self._get_notify_service_for_device(device_id)
        if not service_name:
            return

        # Récupérer la question de CE joueur
        question = self.player_current_question.get(player_num)
        if not question:
            _LOGGER.warning(f"No current question for player {player_num}")
            return

        # Identifier la bonne réponse
        correct_answer = question["réponse"]
        all_propositions = question["propositions"]

        # Séparer bonne réponse et mauvaises réponses
        wrong_answers = [p for p in all_propositions if p != correct_answer]

        # Sélectionner 2 mauvaises réponses aléatoirement parmi les 3 disponibles
        selected_wrong = random.sample(wrong_answers, 2)

        # Créer liste de 3 propositions (1 bonne + 2 mauvaises)
        three_choices = [correct_answer] + selected_wrong

        # Mélanger l'ordre pour que la bonne réponse ne soit pas toujours en position A
        random.shuffle(three_choices)

        # Créer mapping A/B/C -> texte de proposition
        choices_map = {
            "A": three_choices[0],
            "B": three_choices[1],
            "C": three_choices[2]
        }

        # Stocker le mapping pour validation ultérieure
        self.player_displayed_choices[player_num] = choices_map

        _LOGGER.debug(f"Player {player_num} choices: {choices_map}")

        # Format message avec question et 3 options
        message = f"{question['question']}\n\n"
        message += f"A) {three_choices[0]}\n"
        message += f"B) {three_choices[1]}\n"
        message += f"C) {three_choices[2]}"

        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "title": f"🎮 Question {self.player_question_index[player_num] + 1}/{len(self.questions_pool)}",
                "message": message,
                "data": {
                    "actions": [
                        {"action": f"TRIVIA_ANSWER_A_{player_num}", "title": "A"},
                        {"action": f"TRIVIA_ANSWER_B_{player_num}", "title": "B"},
                        {"action": f"TRIVIA_ANSWER_C_{player_num}", "title": "C"},
                    ],
                    "tag": f"trivia_question_{player_num}",  # Tag unique par joueur
                    "persistent": True,
                },
            },
        )

    async def _send_answer_feedback(
        self, player_num: int, device_id: str, is_correct: bool,
        player_answer: str, correct_answer: str
    ) -> None:
        """Send feedback notification after player answers."""
        service_name = await self._get_notify_service_for_device(device_id)
        if not service_name:
            return

        # Supprimer la notification de question active
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "message": "clear_notification",
                "data": {
                    "tag": f"trivia_question_{player_num}"  # Tag unique par joueur
                },
            },
        )

        # Petite pause pour laisser l'app traiter
        await asyncio.sleep(0.3)

        # Préparer le message de feedback selon le résultat
        if is_correct:
            title = "✅ Bonne réponse!"
            message = f"Bravo! La réponse était bien:\n{correct_answer}"
            color = "#4CAF50"  # Vert
            icon = "mdi:check-circle"
        else:
            title = "❌ Mauvaise réponse"
            message = f"Votre réponse: {player_answer}\n\n"
            message += f"La bonne réponse était:\n{correct_answer}"
            color = "#F44336"  # Rouge
            icon = "mdi:close-circle"

        # Envoyer la notification de feedback
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "title": title,
                "message": message,
                "data": {
                    "tag": f"trivia_feedback_{player_num}",  # Tag unique par joueur
                    "notification_icon": icon,
                    "color": color,
                    "timeout": 5,  # Auto-dismiss après 5 secondes
                },
            },
        )

        _LOGGER.debug(f"Feedback sent to player {player_num}: {'correct' if is_correct else 'incorrect'}")

    async def check_answer(self, player: int, answer: str) -> None:
        """Check a player's answer using the 3-choice mapping."""
        # Vérifier que ce joueur a une question active
        if player not in self.player_current_question:
            _LOGGER.warning(f"No current question for player {player}")
            return

        # Récupérer le mapping des choix affichés pour ce joueur
        if player not in self.player_displayed_choices:
            _LOGGER.warning(f"No displayed choices found for player {player}")
            return

        choices_map = self.player_displayed_choices[player]

        # Vérifier que la réponse est valide (A, B, ou C)
        if answer not in choices_map:
            _LOGGER.warning(f"Invalid answer format: {answer} (expected A, B, or C)")
            return

        # Récupérer le texte de la proposition sélectionnée
        player_answer = choices_map[answer]
        correct_answer = self.player_current_question[player]["réponse"]

        # Vérifier si la réponse est correcte
        is_correct = player_answer == correct_answer

        if is_correct:
            self.scores[player] = self.scores.get(player, 0) + 1
            _LOGGER.info(f"Player {player} answered correctly! ({answer}: {player_answer})")
        else:
            _LOGGER.info(f"Player {player} answered incorrectly. ({answer}: {player_answer} != {correct_answer})")

        # Envoyer le feedback au joueur qui a répondu
        device_id = self.players[player - 1]  # player_num est 1-indexed
        await self._send_answer_feedback(
            player, device_id, is_correct, player_answer, correct_answer
        )

        # Attendre 7 secondes pour laisser le temps de lire le feedback
        await asyncio.sleep(7)

        # Incrémenter l'index de question pour CE joueur uniquement
        self.player_question_index[player] += 1
        self._update_listeners()

        # Envoyer la question suivante seulement à CE joueur
        await self.next_question(player)

    async def stop_game(self) -> None:
        """Stop the game and show final scores."""
        if not self.game_active:
            return

        _LOGGER.info(f"Game finished. Final scores: {self.scores}")
        self.game_active = False

        # Send final scores to all players
        for i, device_id in enumerate(self.players):
            await self._send_final_score(i + 1, device_id)

        # Attendre 7 secondes pour que les joueurs lisent leur score individuel
        await asyncio.sleep(7)

        # Envoyer le classement à tous les joueurs
        for i, device_id in enumerate(self.players):
            await self._send_ranking(i + 1, device_id)

        # Nettoyer l'état par joueur
        self.player_question_index = {}
        self.player_current_question = {}
        self.player_finished = {}
        self._update_listeners()


    async def _send_final_score(self, player_num: int, device_id: str) -> None:
        """Send final score to a player."""
        service_name = await self._get_notify_service_for_device(device_id)
        if not service_name:
            return

        score = self.scores.get(player_num, 0)
        total = len(self.questions_pool)

        # D'abord, supprimer la notification de question active
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "message": "clear_notification",
                "data": {
                    "tag": f"trivia_question_{player_num}"  # Tag unique par joueur
                },
            },
        )

        # Petite pause pour laisser l'app traiter la suppression
        await asyncio.sleep(0.5)

        # Ensuite, envoyer le score final avec tag différent
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "title": "🏆 Fin du jeu!",
                "message": f"Votre score: {score}/{total}",
                "data": {
                    "tag": f"trivia_score_{player_num}",  # Tag unique par joueur
                    "notification_icon": "mdi:trophy",
                    "color": "#FFD700",  # Or/Gold
                },
            },
        )

    async def _send_ranking(self, player_num: int, device_id: str) -> None:
        """Send final ranking to a player showing all players' scores."""
        service_name = await self._get_notify_service_for_device(device_id)
        if not service_name:
            return

        total = len(self.questions_pool)

        # Créer liste des scores avec numéro de joueur
        player_scores = []
        for p_num in range(1, self.num_players + 1):
            score = self.scores.get(p_num, 0)
            player_scores.append((p_num, score))

        # Trier par score décroissant
        player_scores.sort(key=lambda x: x[1], reverse=True)

        # Construire le message de classement
        ranking_message = ""
        medals = ["🥇", "🥈", "🥉"]

        for position, (p_num, score) in enumerate(player_scores, start=1):
            # Utiliser médailles pour les 3 premiers, sinon numéro de position
            position_icon = medals[position - 1] if position <= 3 else f"{position}."
            ranking_message += f"{position_icon} Joueur {p_num}: {score}/{total}\n"

        # Supprimer la notification de score individuel
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "message": "clear_notification",
                "data": {
                    "tag": f"trivia_score_{player_num}"  # Tag unique par joueur
                },
            },
        )

        # Petite pause
        await asyncio.sleep(0.5)

        # Envoyer le classement
        await self.hass.services.async_call(
            "notify",
            service_name,
            {
                "title": "📊 Classement Final",
                "message": ranking_message.strip(),
                "data": {
                    "tag": "trivia_ranking",
                    "notification_icon": "mdi:podium",
                    "color": "#9C27B0",  # Violet
                },
            },
        )