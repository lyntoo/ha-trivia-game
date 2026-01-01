# 🎮 Trivia Game - Intégration Home Assistant

Intégration complète Home Assistant pour jeu de quiz interactif avec notifications push.

## 📋 Fonctionnalités

- ✅ Intégration complète avec Config Flow
- ✅ Interface graphique de configuration
- ✅ Panel de jeu dédié
- ✅ 1 à 4 joueurs simultanés
- 📱 Notifications push avec boutons de réponse (A/B/C/D)
- 📚 29 fichiers de questions OpenQuizzDB
- 🎯 3 niveaux de difficulté (débutant, confirmé, expert)
- 🏆 Système de score automatique
- ⚙️ Nombre de questions configurable (1 à 50)
- 📊 Sensors pour l'état du jeu et les scores
- 🔌 Services Home Assistant dédiés

## 🚀 Installation

### 1. Copier les Fichiers

```bash
# Depuis /home/lyntoo/ha-projects/Trivia/
scp -r custom_components/trivia root@$HA_IP:/homeassistant/custom_components/
```

### 2. Copier les Questions

```bash
# Créer le répertoire
ssh root@$HA_IP "mkdir -p /homeassistant/trivia/questions"

# Copier les fichiers JSON
scp questions/*.json root@$HA_IP:/homeassistant/trivia/questions/
```

### 3. Redémarrer Home Assistant

```bash
ssh root@$HA_IP "ha core restart"
```

## ⚙️ Configuration

### Via l'Interface HA

1. Aller dans **Paramètres → Appareils et services**
2. Cliquer sur **+ Ajouter une intégration**
3. Chercher **Trivia Game**
4. Suivre l'assistant de configuration
   - Chemin des questions: `/homeassistant/trivia/questions` (par défaut)

### Vérifier l'Installation

Après redémarrage, vérifier que l'intégration apparaît dans:
- **Paramètres → Appareils et services → Trivia Game**
- Les services `trivia.*` sont disponibles
- Les sensors `sensor.trivia_*` sont créés

## 🎮 Utilisation

### Services Disponibles

#### `trivia.start_game`
Démarre une nouvelle partie.

**Paramètres:**
- `num_players` (requis): Nombre de joueurs (1-4)
- `question_file` (requis): Nom du fichier JSON (ex: `openquizzdb_1001.json`)
- `difficulty` (optionnel): `débutant`, `confirmé`, ou `expert` (défaut: `débutant`)
- `num_questions` (optionnel): Nombre de questions (1-50, défaut: 10)
- `players_devices` (requis): Liste des entités mobile_app (ex: `["mobile_app_armor_24"]`)

**Exemple:**
```yaml
service: trivia.start_game
data:
  num_players: 2
  question_file: "openquizzdb_1001.json"
  difficulty: "confirmé"
  num_questions: 15
  players_devices:
    - mobile_app_armor_24
    - mobile_app_iphone_player2
```

#### `trivia.stop_game`
Arrête la partie en cours.

#### `trivia.next_question`
Envoie la question suivante (appelé automatiquement).

#### `trivia.check_answer`
Vérifie une réponse (appelé automatiquement par les notifications).

**Paramètres:**
- `player`: Numéro du joueur (1-4)
- `answer`: Texte de la réponse

### Sensors Créés

- `sensor.trivia_game_state`: État du jeu (`idle` ou `playing`)
  - Attributs: `current_question_index`, `total_questions`, `num_players`

- `sensor.trivia_current_question`: Question actuelle
  - Attributs: `propositions`, `correct_answer`, `anecdote`

- `sensor.trivia_player1_score` à `sensor.trivia_player4_score`: Scores des joueurs
  - Attributs: `player_number`, `device`

### Automations Suggérées

**Traiter les réponses des notifications:**

```yaml
automation:
  - alias: "Trivia - Traiter réponse notification"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: TRIVIA_ANSWER_A
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: TRIVIA_ANSWER_B
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: TRIVIA_ANSWER_C
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: TRIVIA_ANSWER_D
    action:
      - variables:
          action_letter: >
            {{ trigger.event.data.action.replace('TRIVIA_ANSWER_', '') }}
          answer_text: >
            {% set q = state_attr('sensor.trivia_current_question', 'propositions') %}
            {% if action_letter == 'A' %}{{ q[0] }}
            {% elif action_letter == 'B' %}{{ q[1] }}
            {% elif action_letter == 'C' %}{{ q[2] }}
            {% elif action_letter == 'D' %}{{ q[3] }}
            {% endif %}
      - service: trivia.check_answer
        data:
          player: 1  # Déterminer dynamiquement le joueur
          answer: "{{ answer_text }}"
```

## 📱 Panel de Jeu

Accéder au panel via:
- **Sidebar → Trivia Game** (si configuré)
- **URL:** `http://IP_HA:8123/trivia_panel`

Le panel permet:
- Configuration graphique du jeu
- Démarrage/arrêt de partie
- Affichage de la question actuelle
- Affichage des scores en temps réel

## 📂 Structure des Fichiers

```
custom_components/trivia/
├── __init__.py          # Setup principal, coordinator, services
├── manifest.json        # Métadonnées de l'intégration
├── const.py            # Constantes
├── config_flow.py      # Interface de configuration
├── sensor.py           # Sensors (état, question, scores)
├── services.yaml       # Définition des services
├── translations/       # Traductions
│   ├── en.json
│   └── fr.json
└── www/               # Panel frontend
    └── trivia-panel.html
```

## 🐛 Dépannage

### L'intégration n'apparaît pas

- Vérifier que les fichiers sont dans `/config/custom_components/trivia/`
- Vérifier les logs: **Paramètres → Système → Logs**
- Rechercher "trivia" dans les logs
- Redémarrer HA après la copie des fichiers

### Les notifications ne s'affichent pas

- Vérifier le nom de l'entité mobile_app (ex: `mobile_app_armor_24`)
- Tester manuellement: **Outils de développement → Services → notify.XXX**
- Vérifier que l'appareil est en ligne

### Les questions ne se chargent pas

- Vérifier le chemin: `/homeassistant/trivia/questions/`
- Vérifier les permissions: `chmod 644 /homeassistant/trivia/questions/*.json`
- Vérifier le format JSON des fichiers

### Erreur "path_not_found"

Le chemin des questions n'existe pas. Créer le répertoire:
```bash
ssh root@$HA_IP "mkdir -p /homeassistant/trivia/questions"
```

## 📚 Format OpenQuizzDB

Les fichiers de questions utilisent le format OpenQuizzDB:

```json
{
  "quizz": {
    "fr": {
      "débutant": [
        {
          "id": 1,
          "question": "Quelle est la capitale de la France ?",
          "propositions": ["Paris", "Lyon", "Marseille", "Nice"],
          "réponse": "Paris",
          "anecdote": "Paris est la capitale depuis..."
        }
      ],
      "confirmé": [...],
      "expert": [...]
    }
  }
}
```

## 🔧 Développement

### Tester Localement

```bash
# Valider le code
cd /home/lyntoo/ha-projects/Trivia/custom_components/trivia
python3 -m py_compile *.py

# Copier vers HA
scp -r ../trivia root@$HA_IP:/homeassistant/custom_components/
```

### Ajouter de Nouvelles Questions

1. Créer un fichier JSON au format OpenQuizzDB
2. Le placer dans `/homeassistant/trivia/questions/`
3. Utiliser le nom du fichier dans `question_file` lors du démarrage

## 📄 Licence

- **Code Trivia:** Libre d'utilisation
- **Questions OpenQuizzDB:** CC BY-SA (https://www.openquizzdb.org)

## 🙏 Crédits

- Questions: OpenQuizzDB (Philippe Bresoux)
- Développement: Trivia Game pour Home Assistant

## 📞 Support

En cas de problème:
1. Consulter les logs HA
2. Vérifier l'état des sensors
3. Tester les services manuellement

Bon jeu! 🎉
