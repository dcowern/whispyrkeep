"""
Tests for Universe model.

Tests the Universe model with tone profiles, rules profiles, and calendar settings.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.universes.models import Universe, UniverseHardCanonDoc

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        username="testuser",
    )


@pytest.fixture
def sample_tone_profile():
    """Sample tone profile for testing."""
    return {
        "grimdark_cozy": 0.3,  # 0 = grimdark, 1 = cozy
        "comedy_serious": 0.7,  # 0 = comedy, 1 = serious
        "low_high_magic": 0.5,  # 0 = low magic, 1 = high magic
        "sandbox_railroad": 0.4,  # 0 = sandbox, 1 = railroad
        "combat_roleplay": 0.6,  # 0 = combat focus, 1 = roleplay focus
    }


@pytest.fixture
def sample_rules_profile():
    """Sample rules profile for testing."""
    return {
        "encumbrance": "variant",  # standard, variant, ignored
        "rest_variant": "standard",  # standard, gritty, epic
        "critical_hits": "standard",  # standard, max_damage, brutal
        "flanking": True,
        "multiclassing": True,
        "feats": True,
        "homebrew_allowed": True,
    }


@pytest.fixture
def sample_calendar_profile():
    """Sample calendar profile for testing."""
    return {
        "calendar_type": "gregorian",
        "months_per_year": 12,
        "days_per_month": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
        "month_names": [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ],
        "weekday_names": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "current_year": 1374,
        "epoch_name": "Dale Reckoning",
    }


@pytest.mark.django_db
class TestUniverseModel:
    """Tests for the Universe model."""

    def test_create_basic_universe(self, user):
        """Test creating a basic universe with minimal fields."""
        universe = Universe.objects.create(
            user=user,
            name="Test World",
            description="A test world for adventures",
        )

        assert universe.name == "Test World"
        assert universe.description == "A test world for adventures"
        assert universe.user == user
        assert str(universe) == "Test World"

    def test_universe_uuid_pk(self, user):
        """Test that universe has UUID primary key."""
        universe = Universe.objects.create(
            user=user,
            name="UUID Test",
        )

        # UUID should be a valid UUID string (36 chars with hyphens)
        assert len(str(universe.id)) == 36
        assert "-" in str(universe.id)

    def test_universe_with_tone_profile(self, user, sample_tone_profile):
        """Test universe with tone profile settings."""
        universe = Universe.objects.create(
            user=user,
            name="Toned World",
            tone_profile_json=sample_tone_profile,
        )

        assert universe.tone_profile_json["grimdark_cozy"] == 0.3
        assert universe.tone_profile_json["comedy_serious"] == 0.7
        assert universe.tone_profile_json["low_high_magic"] == 0.5

    def test_universe_with_rules_profile(self, user, sample_rules_profile):
        """Test universe with rules profile settings."""
        universe = Universe.objects.create(
            user=user,
            name="Rules World",
            rules_profile_json=sample_rules_profile,
        )

        assert universe.rules_profile_json["encumbrance"] == "variant"
        assert universe.rules_profile_json["flanking"] is True
        assert universe.rules_profile_json["multiclassing"] is True

    def test_universe_with_calendar_profile(self, user, sample_calendar_profile):
        """Test universe with calendar profile settings."""
        universe = Universe.objects.create(
            user=user,
            name="Calendar World",
            calendar_profile_json=sample_calendar_profile,
        )

        assert universe.calendar_profile_json["calendar_type"] == "gregorian"
        assert universe.calendar_profile_json["current_year"] == 1374
        assert len(universe.calendar_profile_json["month_names"]) == 12

    def test_universe_with_current_time(self, user):
        """Test universe with current universe time."""
        current_time = {
            "year": 1374,
            "month": 6,
            "day": 15,
            "hour": 14,
            "minute": 30,
        }
        universe = Universe.objects.create(
            user=user,
            name="Time World",
            current_universe_time=current_time,
        )

        assert universe.current_universe_time["year"] == 1374
        assert universe.current_universe_time["month"] == 6

    def test_universe_json_fields_default_empty(self, user):
        """Test that JSON fields default to empty dicts."""
        universe = Universe.objects.create(
            user=user,
            name="Empty JSON World",
        )

        assert universe.tone_profile_json == {}
        assert universe.rules_profile_json == {}
        assert universe.calendar_profile_json == {}
        assert universe.current_universe_time == {}

    def test_universe_canonical_lore_version(self, user):
        """Test canonical lore version starts at 0."""
        universe = Universe.objects.create(
            user=user,
            name="Lore World",
        )

        assert universe.canonical_lore_version == 0

        # Increment version
        universe.canonical_lore_version = 1
        universe.save()
        universe.refresh_from_db()
        assert universe.canonical_lore_version == 1

    def test_universe_archive(self, user):
        """Test archiving a universe."""
        universe = Universe.objects.create(
            user=user,
            name="Archive World",
        )

        assert universe.is_archived is False

        universe.is_archived = True
        universe.save()
        universe.refresh_from_db()
        assert universe.is_archived is True

    def test_universe_timestamps(self, user):
        """Test universe has created_at and updated_at timestamps."""
        universe = Universe.objects.create(
            user=user,
            name="Timestamped World",
        )

        assert universe.created_at is not None
        assert universe.updated_at is not None

        original_updated = universe.updated_at
        universe.name = "Updated Name"
        universe.save()

        universe.refresh_from_db()
        assert universe.updated_at > original_updated

    def test_universe_user_cascade_delete(self, user):
        """Test that deleting user cascades to universes."""
        universe = Universe.objects.create(
            user=user,
            name="Doomed World",
        )
        universe_id = universe.id

        user.delete()

        assert not Universe.objects.filter(id=universe_id).exists()

    def test_multiple_universes_per_user(self, user):
        """Test user can have multiple universes."""
        universe1 = Universe.objects.create(
            user=user,
            name="World One",
        )
        universe2 = Universe.objects.create(
            user=user,
            name="World Two",
        )

        assert user.universes.count() == 2
        assert universe1 in user.universes.all()
        assert universe2 in user.universes.all()

    def test_full_universe_creation(
        self,
        user,
        sample_tone_profile,
        sample_rules_profile,
        sample_calendar_profile,
    ):
        """Test creating a fully-configured universe."""
        universe = Universe.objects.create(
            user=user,
            name="Complete World",
            description="A fully configured test world",
            tone_profile_json=sample_tone_profile,
            rules_profile_json=sample_rules_profile,
            calendar_profile_json=sample_calendar_profile,
            current_universe_time={"year": 1374, "month": 1, "day": 1},
            canonical_lore_version=5,
        )

        assert universe.name == "Complete World"
        assert universe.tone_profile_json == sample_tone_profile
        assert universe.rules_profile_json == sample_rules_profile
        assert universe.calendar_profile_json == sample_calendar_profile
        assert universe.canonical_lore_version == 5


@pytest.mark.django_db
class TestUniverseHardCanonDoc:
    """Tests for UniverseHardCanonDoc model."""

    def test_create_hard_canon_doc(self, user):
        """Test creating a hard canon document."""
        universe = Universe.objects.create(user=user, name="Canon World")
        doc = UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="upload",
            title="World History",
            raw_text="In the beginning, the gods created the world...",
            checksum="abc123def456",
        )

        assert doc.title == "World History"
        assert doc.universe == universe
        assert doc.source_type == "upload"
        assert doc.never_compact is True  # Default
        assert str(doc) == "World History (Canon World)"

    def test_hard_canon_source_types(self, user):
        """Test different source types for canon docs."""
        universe = Universe.objects.create(user=user, name="Canon World")

        # User upload
        upload_doc = UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="upload",
            title="Uploaded Lore",
            raw_text="...",
            checksum="abc",
        )
        assert upload_doc.source_type == "upload"

        # Worldgen
        worldgen_doc = UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="worldgen",
            title="Generated Lore",
            raw_text="...",
            checksum="def",
        )
        assert worldgen_doc.source_type == "worldgen"

        # User edit
        edit_doc = UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="user_edit",
            title="Edited Lore",
            raw_text="...",
            checksum="ghi",
        )
        assert edit_doc.source_type == "user_edit"

    def test_hard_canon_cascade_delete(self, user):
        """Test that deleting universe deletes canon docs."""
        universe = Universe.objects.create(user=user, name="Canon World")
        doc = UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="upload",
            title="Test Doc",
            raw_text="...",
            checksum="abc",
        )
        doc_id = doc.id

        universe.delete()

        assert not UniverseHardCanonDoc.objects.filter(id=doc_id).exists()

    def test_multiple_canon_docs_per_universe(self, user):
        """Test universe can have multiple canon docs."""
        universe = Universe.objects.create(user=user, name="Canon World")

        for i in range(3):
            UniverseHardCanonDoc.objects.create(
                universe=universe,
                source_type="upload",
                title=f"Doc {i}",
                raw_text=f"Content {i}",
                checksum=f"checksum{i}",
            )

        assert universe.hard_canon_docs.count() == 3
