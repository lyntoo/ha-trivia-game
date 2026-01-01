"""Constants for the Trivia Game integration."""

DOMAIN = "trivia"

# Service names
SERVICE_START_GAME = "start_game"
SERVICE_STOP_GAME = "stop_game"
SERVICE_NEXT_QUESTION = "next_question"
SERVICE_CHECK_ANSWER = "check_answer"

# Default values
DEFAULT_NUM_QUESTIONS = 10
DEFAULT_DIFFICULTY = "débutant"

# Difficulty levels
DIFFICULTY_BEGINNER = "débutant"
DIFFICULTY_CONFIRMED = "confirmé"
DIFFICULTY_EXPERT = "expert"

DIFFICULTIES = [DIFFICULTY_BEGINNER, DIFFICULTY_CONFIRMED, DIFFICULTY_EXPERT]
