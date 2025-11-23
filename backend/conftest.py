"""
Pytest configuration and fixtures for WhispyrKeep tests.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def srd_ability_scores(db):
    """Create SRD ability scores for testing."""
    from apps.srd.models import AbilityScore

    ability_data = [
        {"abbreviation": "str", "name": "Strength", "description": "Physical power"},
        {"abbreviation": "dex", "name": "Dexterity", "description": "Agility and reflexes"},
        {"abbreviation": "con", "name": "Constitution", "description": "Health and stamina"},
        {"abbreviation": "int", "name": "Intelligence", "description": "Mental acuity"},
        {"abbreviation": "wis", "name": "Wisdom", "description": "Perception and insight"},
        {"abbreviation": "cha", "name": "Charisma", "description": "Force of personality"},
    ]
    return {a["abbreviation"]: AbilityScore.objects.create(**a) for a in ability_data}


@pytest.fixture
def srd_skills(db, srd_ability_scores):
    """Create SRD skills for testing."""
    from apps.srd.models import Skill

    skill_data = [
        ("Acrobatics", "dex"),
        ("Animal Handling", "wis"),
        ("Arcana", "int"),
        ("Athletics", "str"),
        ("Deception", "cha"),
        ("History", "int"),
        ("Insight", "wis"),
        ("Intimidation", "cha"),
        ("Investigation", "int"),
        ("Medicine", "wis"),
        ("Nature", "int"),
        ("Perception", "wis"),
        ("Performance", "cha"),
        ("Persuasion", "cha"),
        ("Religion", "int"),
        ("Sleight of Hand", "dex"),
        ("Stealth", "dex"),
        ("Survival", "wis"),
    ]
    return [
        Skill.objects.create(name=name, ability_score=srd_ability_scores[abbr])
        for name, abbr in skill_data
    ]


@pytest.fixture
def srd_species(db):
    """Create basic SRD species for testing."""
    from apps.srd.models import Species

    species_data = [
        {"name": "Human", "description": "Versatile and ambitious", "size": "medium", "speed": 30},
        {"name": "Dwarf", "description": "Sturdy and steadfast", "size": "medium", "speed": 25},
        {"name": "Elf", "description": "Graceful and long-lived", "size": "medium", "speed": 30},
        {"name": "Halfling", "description": "Small but brave", "size": "small", "speed": 25},
    ]
    return [Species.objects.create(**data) for data in species_data]


@pytest.fixture
def srd_classes(db):
    """Create basic SRD character classes for testing."""
    from apps.srd.models import CharacterClass

    class_data = [
        {"name": "Fighter", "description": "Master of martial combat", "hit_die": 10},
        {"name": "Wizard", "description": "Scholarly magic-user", "hit_die": 6},
        {"name": "Rogue", "description": "Stealthy and cunning", "hit_die": 8},
        {"name": "Cleric", "description": "Divine spellcaster", "hit_die": 8},
        {"name": "Barbarian", "description": "Primal warrior", "hit_die": 12},
    ]
    return [CharacterClass.objects.create(**data) for data in class_data]


@pytest.fixture
def srd_backgrounds(db):
    """Create basic SRD backgrounds for testing."""
    from apps.srd.models import Background

    background_data = [
        {"name": "Soldier", "description": "Military training"},
        {"name": "Acolyte", "description": "Religious upbringing"},
        {"name": "Criminal", "description": "Shady past"},
        {"name": "Noble", "description": "Born to privilege"},
    ]
    return [Background.objects.create(**data) for data in background_data]


@pytest.fixture
def srd_data(srd_ability_scores, srd_skills, srd_species, srd_classes, srd_backgrounds):
    """Combined fixture providing all basic SRD data."""
    return {
        "ability_scores": srd_ability_scores,
        "skills": srd_skills,
        "species": srd_species,
        "classes": srd_classes,
        "backgrounds": srd_backgrounds,
    }


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        display_name="Test User",
    )


@pytest.fixture
def api_client():
    """DRF API test client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """API client with authenticated user."""
    api_client.force_authenticate(user=user)
    return api_client
