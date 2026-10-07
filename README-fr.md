# 🔥 Pilot Wire Climate

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)

Une entrée (helper) Home Assistant qui transforme un module fil pilote en véritable entité `climate` : modes, marche/arrêt, détection de chauffe et, en option, température et humidité.

[![Ouvrir Home Assistant et afficher ce dépôt dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Diaoul&repository=hass-pilot-wire-climate&category=integration)

## ✨ Fonctionnalités

- 🎛️ **Modes depuis le select** - Confort, Confort -1 °C, Confort -2 °C, Éco et Hors-gel deviennent des modes du thermostat
- 🔛 **Marche/Arrêt** - L'arrêt est le mode HVAC `off` ; le rallumage revient au dernier mode, même après un redémarrage
- 🔥 **Détection de chauffe** - Un capteur de puissance et un seuil distinguent la chauffe du repos
- 🌡️ **Température et humidité** - Capteurs optionnels affichés sur le thermostat
- 🧩 **Seulement ce que le module accepte** - Les modes absents du select ne sont pas proposés
- 🏷️ **Rattaché au module** - Le thermostat rejoint l'appareil du select, en prend le nom et masque le select devenu redondant
- 🔄 **Suit les renommages** - Renommer le select ou un capteur met à jour le thermostat au lieu de le casser
- 🔌 **Gestion de la disponibilité** - Le thermostat est indisponible quand son select l'est, et une mesure s'efface quand son capteur est indisponible ou ne donne pas de nombre
- ⚙️ **Modifiable** - Tous les réglages, select compris, se changent ensuite depuis les options de l'entrée

## 📦 Installation

Cliquez sur le bouton ci-dessus pour ajouter ce dépôt à HACS, puis téléchargez **Pilot Wire Climate** et redémarrez Home Assistant.

**Nécessite Home Assistant 2026.10 ou plus récent** (vérifié par HACS).

> **Si vous venez de [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate) :**
> ce fork n'a ni configuration YAML ni mode `none`. Recréez les thermostats
> YAML en tant qu'entrées, et faites passer les automatisations qui utilisent
> le mode `none` au mode HVAC `off`. Les thermostats créés depuis l'interface
> sont migrés automatiquement.

## 🚀 Démarrage rapide

1. Allez dans **Paramètres** → **Appareils et services** → [**Entrées**](https://my.home-assistant.io/redirect/helpers/)
2. **Créer une entrée** → **Thermostat Fil Pilote**
3. **Choisissez le select fil pilote du module** (obligatoire) - un `select` ou un `input_select` avec des options fil pilote, non utilisé par un autre thermostat
4. **(Optionnel)** Choisissez un capteur de température, d'humidité et de puissance
5. **(Optionnel)** Réglez le seuil de puissance, le mode par défaut et l'affichage des modes Confort -1 °C et -2 °C

Le thermostat apparaît sur l'appareil du module, sous son nom.

## 🔧 Options

| Option | Par défaut | Description |
| :----- | :--------- | :---------- |
| Entité de sélection | obligatoire | Le `select` ou `input_select` fil pilote du module |
| Capteur de température | aucun | Affiché comme température actuelle, dans l'unité du capteur, ou en °C pour un capteur en kelvins |
| Capteur d'humidité | aucun | Affiché comme humidité actuelle |
| Capteur de puissance | aucun | Distingue la chauffe du repos |
| Modes supplémentaires | activé | Propose Confort -1 °C et Confort -2 °C quand le select les a |
| Seuil de puissance | 0 W | Puissance au-delà de laquelle le radiateur est considéré en chauffe, en watts quelle que soit l'unité du capteur |
| Mode par défaut | Confort | Mode utilisé pour allumer un thermostat qui n'a pas de mode précédent ; doit exister dans le select et être proposé par le thermostat |

## 🧠 Fonctionnement

Le thermostat est une vue du select : la seule chose qu'il conserve lui-même est le dernier mode.

| Option du select | Thermostat |
| :--------------- | :--------- |
| `comfort`, `Comfort` | Chauffe, Confort |
| `comfort_-1`, `ComfortMinus1` | Chauffe, Confort -1 °C |
| `comfort_-2`, `ComfortMinus2` | Chauffe, Confort -2 °C |
| `eco`, `Eco` | Chauffe, Éco |
| `frost_protection`, `FrostProtection` | Chauffe, Hors-gel (`away`) |
| `off`, `Off` | Arrêt |

- **Choisir un mode** sélectionne l'option correspondante, ce qui rallume aussi un thermostat arrêté ; choisir le mode en cours n'envoie rien
- **Allumer** revient au dernier mode, ou au mode par défaut s'il n'y en a pas ; allumer un thermostat déjà en chauffe n'envoie rien
- **L'état de chauffe** vaut `heating` au-dessus du seuil de puissance, même thermostat arrêté, ce qui révèle un module qui ignore l'arrêt. Sinon il vaut `off` quand le thermostat est arrêté, avec ou sans capteur de puissance, et `idle` sous le seuil
- **Une option inconnue**, ou celle d'un mode non proposé, s'affiche en chauffe sans mode ; une option inconnue est aussi signalée par un avertissement dans les journaux

## 🔌 Compatibilité

Tout module qui expose son mode fil pilote sous forme de select avec les options ci-dessus, notamment :

- **Equation** : SIN-4-FP-21_EQU
- **Legrand** : 064882
- **NodOn** : SIN-4-FP-20, SIN-4-FP-21

## ⚙️ Détails techniques

- **Pas d'interrogation :** le thermostat réagit uniquement aux changements d'état de son select et de ses capteurs
- **Démarrage :** les sources sont lues une fois Home Assistant démarré
- **Reprise après redémarrage :** le dernier mode est conservé, donc rallumer après un redémarrage y revient
- **Suppression :** supprimer l'entrée réaffiche le select, sauf si vous l'aviez masqué vous-même

## 🤝 Support

En cas de problème :
- Activez les journaux de débogage pour `custom_components.pilot_wire_climate` et consultez-les
- Vérifiez les options du select dans **Outils de développement** → **États**
- Ouvrez un ticket sur [GitHub](https://github.com/Diaoul/hass-pilot-wire-climate/issues)

---

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

---

Fork de [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate), fait avec ❤️ pour la communauté Home Assistant
