from source_policy import (
    OFFICIAL_SOURCE_PRIORITY,
    PORTAL_SOURCE_PRIORITY,
    should_replace_primary,
)


def test_official_replaces_portal_primary_source():
    assert should_replace_primary(
        PORTAL_SOURCE_PRIORITY,
        OFFICIAL_SOURCE_PRIORITY,
    )


def test_portal_does_not_replace_official_primary_source():
    assert not should_replace_primary(
        OFFICIAL_SOURCE_PRIORITY,
        PORTAL_SOURCE_PRIORITY,
    )


def test_equal_priority_can_refresh_primary_metadata():
    assert should_replace_primary(
        OFFICIAL_SOURCE_PRIORITY,
        OFFICIAL_SOURCE_PRIORITY,
    )
