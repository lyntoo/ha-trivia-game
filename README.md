# 🎮 Trivia Game pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/lyntoo/ha-trivia-game.svg)](https://github.com/lyntoo/ha-trivia-game/releases)
[![License](https://img.shields.io/github/license/lyntoo/ha-trivia-game.svg)](LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lyntoo&repository=ha-trivia-game&category=integration)

Intégration Home Assistant pour créer des parties de quiz multijoueur interactives avec notifications push sur mobile!

## ✨ Fonctionnalités

- 🎯 **Multijoueur indépendant** - Jusqu'à 4 joueurs, chacun avec sa propre progression
- 📱 **Notifications push** - Questions et réponses directement sur vos appareils mobiles
- ✅ **Feedback instantané** - Réponse correcte/incorrecte avec 7 secondes de lecture
- 🏆 **Classement final** - Score individuel puis podium avec médailles 🥇🥈🥉
- 📚 **29 fichiers de questions** - Culture générale via OpenQuizzDB (français)
- 🎚️ **3 niveaux de difficulté** - Débutant, Intermédiaire, Confirmé
- ⚙️ **Configuration flexible** - 1 à 50 questions par partie
- 🔄 **Autonome** - Aucun helper externe requis!

## 📦 Installation

### 🚀 Installation en 1 clic (Recommandé)

Cliquez sur ce badge pour installer directement dans votre Home Assistant:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lyntoo&repository=ha-trivia-game&category=integration)

> **Note**: HACS doit être installé. Si ce n'est pas le cas, suivez les instructions ci-dessous.

### Via HACS (Installation manuelle)

1. Ouvrir **HACS** dans Home Assistant
2. Cliquer sur **Intégrations**
3. Cliquer sur les **3 points** en haut à droite → **Dépôts personnalisés**
4. Ajouter l'URL: `https://github.com/lyntoo/ha-trivia-game`
5. Catégorie: **Integration**
6. Cliquer sur **Ajouter**
7. Rechercher **"Trivia Game"** dans HACS
8. Cliquer sur **Télécharger**
9. **Redémarrer** Home Assistant

### Installation Manuelle

1. Télécharger la dernière release depuis [Releases](https://github.com/lyntoo/ha-trivia-game/releases)
2. Copier le dossier `custom_components/trivia` vers votre dossier `config/custom_components/`
3. Redémarrer Home Assistant

## ⚙️ Configuration

### 1. Ajouter l'intégration

1. Aller dans **Paramètres** → **Appareils et services**
2. Cliquer sur **+ Ajouter une intégration**
3. Rechercher **"Trivia Game"**
4. Cliquer sur **Trivia Game** pour l'ajouter

### 2. Configuration du jeu

L'intégration crée automatiquement les entités suivantes:

#### Sélection
- **Fichier de questions** - Choisir parmi 29 fichiers de questions
- **Difficulté** - Débutant / Intermédiaire / Confirmé
- **Joueur 1/2/3/4** - Sélectionner les appareils mobiles

#### Nombres
- **Nombre de joueurs** - 1 à 4
- **Nombre de questions** - 1 à 50

#### Boutons
- **Démarrer le jeu** - Lancer une partie
- **Question suivante** - Passer à la question suivante (debug)
- **Arrêter le jeu** - Terminer la partie en cours

#### Capteurs
- **État du jeu** - Actif / Inactif
- **Question actuelle** - Texte de la question en cours
- **Scores des joueurs** - Score de chaque joueur (1-4)

## 🎮 Utilisation

### Démarrer une partie

1. **Sélectionner le fichier de questions** (ex: Culture générale, Géographie)
2. **Choisir la difficulté** (Débutant, Intermédiaire, Confirmé)
3. **Définir le nombre de questions** (1-50)
4. **Sélectionner les appareils mobiles** des joueurs
5. **Cliquer sur "Démarrer le jeu"**

### Pendant la partie

- Chaque joueur reçoit une **notification push** avec la question
- **3 choix de réponse** (A, B, C) - limite Android
- Cliquer sur la réponse dans la notification
- **Feedback immédiat** (vert = correct ✅ / rouge = incorrect ❌)
- Si incorrect, affiche la **bonne réponse**
- **7 secondes** de pause pour lire le feedback
- **Question suivante automatique** pour ce joueur uniquement

### Fin de partie

1. Chaque joueur termine à son **propre rythme**
2. Quand tous ont fini, envoi du **score individuel** 🏆
3. Attente de **7 secondes**
4. Envoi du **classement complet** avec podium 🥇🥈🥉

## 📚 Format des questions

Les fichiers JSON suivent le format OpenQuizzDB:

```json
{
  "quizz": {
    "fr": {
      "débutant": [
        {
          "question": "Quelle est la capitale de la France ?",
          "propositions": [
            "Paris",
            "Londres",
            "Berlin",
            "Madrid"
          ],
          "réponse": "Paris"
        }
      ]
    }
  }
}
```

### Ajouter vos propres questions

1. Créer un fichier JSON dans `custom_components/trivia/questions/`
2. Suivre le format ci-dessus
3. Minimum 3 niveaux: `débutant`, `intermédiaire`, `confirmé`
4. 4 propositions dont 1 réponse correcte
5. Recharger l'intégration pour voir le nouveau fichier

## 🔧 Services

L'intégration expose les services suivants:

### `trivia.start_game`
Démarrer une partie de trivia

**Paramètres:**
- `players_devices` (optionnel) - Liste des device_id mobiles

### `trivia.stop_game`
Arrêter la partie en cours

### `trivia.next_question`
Passer à la question suivante (debug)

### `trivia.check_answer`
Vérifier la réponse d'un joueur

**Paramètres:**
- `player` (1-4) - Numéro du joueur
- `answer` (A/B/C) - Lettre de la réponse

## 🤝 Contribution

Les contributions sont les bienvenues!

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 🐛 Problèmes connus

- **Android limite** - Maximum 3 boutons par notification (d'où A/B/C au lieu de A/B/C/D)
- **Compatibilité mobile** - Nécessite l'application Home Assistant mobile

## 📝 Changelog

### v1.0.0 (2025-01-01)
- 🎉 Release initiale
- ✅ Support multijoueur indépendant (1-4 joueurs)
- ✅ Notifications push avec feedback
- ✅ Classement final avec podium
- ✅ 29 fichiers de questions OpenQuizzDB
- ✅ 3 niveaux de difficulté

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [OpenQuizzDB](https://www.openquizzdb.org/) pour la base de questions
- La communauté Home Assistant
- Contributeurs et testeurs

## 📧 Support

- 🐛 [Signaler un bug](https://github.com/lyntoo/ha-trivia-game/issues)
- 💡 [Demander une fonctionnalité](https://github.com/lyntoo/ha-trivia-game/issues)
- 💬 [Discussions](https://github.com/lyntoo/ha-trivia-game/discussions)

---

Fait avec ❤️ pour la communauté Home Assistant
