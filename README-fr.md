# README - Intégration Fil Pilote pour Home Assistant

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README-fr.md)

## Vue d'ensemble
Cette intégration pour Home Assistant simplifie l'installation de modules fil pilote pour les systèmes de chauffage, en convertissant automatiquement plusieurs entités (`select` et `power`) en une seule entité `climate`. Une entité `sensor` de température peut également être ajoutée en option. Cette intégration est idéale pour contrôler et surveiller les modules fil pilote de chauffage.

### Caractéristiques principales
- Convertit les entités `select` et `power` en une seule entité `climate`.
- Utilise l'entité `select` pour ajuster les modes prédéfinis du fil pilote.
- Utilise l'entité `power` pour détecter si le chauffage est actif.
- Mode par défaut à l'allumage configurable.
- Seuil de puissance configurable pour déterminer l'état de chauffe.
- Prise en charge optionnelle pour une entité `sensor` de température.

### Compatibilité
L'intégration est compatible avec les appareils suivants ou tout thermostat contrôlable avec une entité de type select:
- **Equation** : SIN-4-FP-21_EQU
- **Legrand** : 064882
- **NodOn** : SIN-4-FP-20, SIN-4-FP-21

## Installation

### Option 1 : Utilisation de HACS (Home Assistant Community Store)
[![Ouvre Home Assistant et charge le repository dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=faizpuru&repository=ha-pilot-wire-climate&category=integration)

1. Utilisez le bouton au dessus ou bien cherchez "Wire Pilot Climate" dans HACS
2. Installez l'intégration, puis redémarrez Home Assistant.

### Option 2 : Installation manuelle
1. Copiez les fichiers de l'intégration dans le répertoire des composants personnalisés de Home Assistant.
2. Redémarrez Home Assistant.
3. Ajoutez l'intégration via l'interface utilisateur de Home Assistant.

## Configuration
Cette intégration se configure uniquement via l'interface utilisateur de Home Assistant.

> [!IMPORTANT]  
> Cette intégration est implémentée comme un **Helper** dans Home Assistant et non comme une intégration personnalisée classique.
> 
> Pour initialiser ce helper, suivez ce chemin dans votre interface Home Assistant :
> 1. Paramètres
> 2. Appareils et Services
> 3. Entrées
> 4. Créer une entrée
> 5. Thermostat Fil Pilote
>
> Une fois configuré, l'entité climate apparaîtra dans l'onglet Entrées. Elle sera également automatiquement liée à l'appareil de l'entité select choisie lors de la configuration.

## 🤝 Contributions
Les contributions sont les bienvenues ! N'hésitez pas à :

- 🐛 Signaler des bugs
- 💡 Suggérer des améliorations
- 🔀 Soumettre des pull requests

## 📄 Licence
Ce projet est sous licence MIT. Consultez le fichier LICENSE pour plus de détails.

---
Si vous trouvez cette intégration utile, pensez à lui donner une ⭐️ sur GitHub !
