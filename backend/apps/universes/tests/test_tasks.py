"""
Tests for universe Celery tasks.

Tests async tasks for worldgen and catalog pre-generation.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.universes.models import (
    HomebrewBackground,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    Universe,
)
from apps.universes.tasks import (
    generate_universe_content_task,
    lock_universe_homebrew_task,
    pregenerate_catalog_task,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        username="testuser",
    )


@pytest.fixture
def universe(user):
    """Create test universe with tone profile."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A test universe for task testing",
        tone_profile_json={
            "grimdark_cozy": 0.5,
            "comedy_serious": 0.5,
            "low_high_magic": 0.7,
            "sandbox_railroad": 0.5,
            "combat_roleplay": 0.5,
            "themes": ["adventure", "magic"],
        },
        rules_profile_json={
            "encumbrance": "variant",
            "rest_variant": "standard",
            "flanking": True,
            "multiclassing": True,
            "feats": True,
            "homebrew_amount": "moderate",
        },
    )


@pytest.fixture
def universe_with_homebrew(universe):
    """Create universe with homebrew content."""
    # Create some homebrew content
    HomebrewSpecies.objects.create(
        universe=universe,
        name="Test Species",
        description="A test species",
        traits_json={"speed": 30},
        is_locked=False,
    )
    HomebrewSpell.objects.create(
        universe=universe,
        name="Test Spell",
        description="A test spell",
        level=1,
        school="evocation",
        is_locked=False,
    )
    HomebrewItem.objects.create(
        universe=universe,
        name="Test Item",
        description="A test item",
        item_type="weapon",
        rarity="common",
        is_locked=False,
    )
    HomebrewMonster.objects.create(
        universe=universe,
        name="Test Monster",
        description="A test monster",
        challenge_rating="1",
        stats_json={"hp": 10, "ac": 12},
        is_locked=False,
    )
    HomebrewFeat.objects.create(
        universe=universe,
        name="Test Feat",
        description="A test feat",
        prerequisites_json={},
        is_locked=False,
    )
    HomebrewBackground.objects.create(
        universe=universe,
        name="Test Background",
        description="A test background",
        feature_name="Test Feature",
        feature_description="A test feature",
        is_locked=False,
    )
    return universe


@pytest.mark.django_db
class TestGenerateUniverseContentTask:
    """Tests for generate_universe_content_task."""

    def test_task_with_valid_inputs(self, user, universe):
        """Test task executes successfully with valid inputs."""
        result = generate_universe_content_task.apply(
            args=[str(user.id), str(universe.id), ["species", "spells"], 3]
        ).get()

        assert result["success"] is True
        assert result["universe_id"] == str(universe.id)
        assert result["content_types"] == ["species", "spells"]
        assert result["max_items_per_type"] == 3

    def test_task_with_all_content_types(self, user, universe):
        """Test task with all content types."""
        all_types = ["species", "classes", "backgrounds", "spells", "items", "monsters", "feats"]
        result = generate_universe_content_task.apply(
            args=[str(user.id), str(universe.id), all_types, 5]
        ).get()

        assert result["success"] is True
        assert result["content_types"] == all_types

    def test_task_with_invalid_user(self, universe):
        """Test task fails with invalid user ID."""
        import uuid

        fake_user_id = str(uuid.uuid4())
        result = generate_universe_content_task.apply(
            args=[fake_user_id, str(universe.id), ["species"], 3]
        ).get()

        assert result["success"] is False
        assert "error" in result

    def test_task_with_invalid_universe(self, user):
        """Test task fails with invalid universe ID."""
        import uuid

        fake_universe_id = str(uuid.uuid4())
        result = generate_universe_content_task.apply(
            args=[str(user.id), fake_universe_id, ["species"], 3]
        ).get()

        assert result["success"] is False
        assert "error" in result

    def test_task_with_wrong_user_universe_combo(self, user, universe):
        """Test task fails when user doesn't own universe."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            username="otheruser",
        )

        result = generate_universe_content_task.apply(
            args=[str(other_user.id), str(universe.id), ["species"], 3]
        ).get()

        assert result["success"] is False
        assert "error" in result

    def test_task_with_empty_content_types(self, user, universe):
        """Test task with empty content types list."""
        result = generate_universe_content_task.apply(
            args=[str(user.id), str(universe.id), [], 3]
        ).get()

        assert result["success"] is True
        assert result["content_types"] == []


@pytest.mark.django_db
class TestPregenerateCatalogTask:
    """Tests for pregenerate_catalog_task."""

    def test_task_executes_successfully(self, user, universe):
        """Test catalog pre-generation task executes."""
        result = pregenerate_catalog_task.apply(
            args=[str(user.id), str(universe.id)]
        ).get()

        assert result["success"] is True
        assert result["universe_id"] == str(universe.id)

    def test_task_generates_all_content_types(self, user, universe):
        """Test task generates all content types."""
        result = pregenerate_catalog_task.apply(
            args=[str(user.id), str(universe.id)]
        ).get()

        expected_types = ["species", "backgrounds", "spells", "items", "monsters", "feats"]
        assert result["content_types"] == expected_types

    def test_task_with_invalid_user(self, universe):
        """Test task fails with invalid user."""
        import uuid

        fake_user_id = str(uuid.uuid4())
        result = pregenerate_catalog_task.apply(
            args=[fake_user_id, str(universe.id)]
        ).get()

        assert result["success"] is False


@pytest.mark.django_db
class TestLockUniverseHomebrewTask:
    """Tests for lock_universe_homebrew_task."""

    def test_lock_all_homebrew(self, universe_with_homebrew):
        """Test locking all homebrew content."""
        result = lock_universe_homebrew_task.apply(
            args=[str(universe_with_homebrew.id)]
        ).get()

        assert result["success"] is True
        assert result["universe_id"] == str(universe_with_homebrew.id)
        assert "locked_counts" in result

        # Check counts
        locked_counts = result["locked_counts"]
        assert locked_counts["species"] == 1
        assert locked_counts["spells"] == 1
        assert locked_counts["items"] == 1
        assert locked_counts["monsters"] == 1
        assert locked_counts["feats"] == 1
        assert locked_counts["backgrounds"] == 1

    def test_locked_content_stays_locked(self, universe_with_homebrew):
        """Test already locked content is not counted again."""
        # Lock everything first
        lock_universe_homebrew_task.apply(
            args=[str(universe_with_homebrew.id)]
        ).get()

        # Lock again
        result = lock_universe_homebrew_task.apply(
            args=[str(universe_with_homebrew.id)]
        ).get()

        # All counts should be 0 since everything was already locked
        locked_counts = result["locked_counts"]
        assert locked_counts["species"] == 0
        assert locked_counts["spells"] == 0
        assert locked_counts["items"] == 0

    def test_verify_is_locked_flag(self, universe_with_homebrew):
        """Test that is_locked flag is actually set."""
        lock_universe_homebrew_task.apply(
            args=[str(universe_with_homebrew.id)]
        ).get()

        # Verify all content is locked
        assert not HomebrewSpecies.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()
        assert not HomebrewSpell.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()
        assert not HomebrewItem.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()
        assert not HomebrewMonster.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()
        assert not HomebrewFeat.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()
        assert not HomebrewBackground.objects.filter(
            universe=universe_with_homebrew, is_locked=False
        ).exists()

    def test_lock_invalid_universe(self):
        """Test locking with invalid universe ID."""
        import uuid

        fake_universe_id = str(uuid.uuid4())
        result = lock_universe_homebrew_task.apply(
            args=[fake_universe_id]
        ).get()

        assert result["success"] is False
        assert "Universe not found" in result["error"]

    def test_lock_empty_universe(self, universe):
        """Test locking universe with no homebrew content."""
        result = lock_universe_homebrew_task.apply(
            args=[str(universe.id)]
        ).get()

        assert result["success"] is True
        # All counts should be 0
        for count in result["locked_counts"].values():
            assert count == 0

    def test_partial_lock(self, universe_with_homebrew):
        """Test locking when some content is already locked."""
        # Lock just the species manually
        HomebrewSpecies.objects.filter(universe=universe_with_homebrew).update(
            is_locked=True
        )

        result = lock_universe_homebrew_task.apply(
            args=[str(universe_with_homebrew.id)]
        ).get()

        # Species count should be 0, others should be 1
        locked_counts = result["locked_counts"]
        assert locked_counts["species"] == 0
        assert locked_counts["spells"] == 1
        assert locked_counts["items"] == 1
