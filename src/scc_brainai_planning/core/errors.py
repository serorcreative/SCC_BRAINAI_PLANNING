"""Hiérarchie d'exceptions de la couche de planification BrainAI."""

from __future__ import annotations


class PlanningError(Exception):
    """Erreur de base de la couche de planification."""


class ConfigError(PlanningError):
    """Configuration absente, illisible ou invalide."""


class SourceUnavailable(PlanningError):
    """Une source (Learning, Reasoning, API) est indisponible."""


class ValidationError(PlanningError):
    """Transition de validation humaine interdite."""


class NotFoundError(PlanningError):
    """Plan ou tâche introuvable."""


class ObjectiveError(PlanningError):
    """Objectif mal formé (but manquant, tâches invalides)."""


class DependencyError(PlanningError):
    """Dépendance invalide (cycle, prérequis introuvable)."""


__all__ = [
    "PlanningError", "ConfigError", "SourceUnavailable", "ValidationError",
    "NotFoundError", "ObjectiveError", "DependencyError",
]
