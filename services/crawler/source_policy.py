OFFICIAL_SOURCE_PRIORITY = 10
PORTAL_SOURCE_PRIORITY = 30
DISCOVERY_SOURCE_PRIORITY = 50
DEMO_SOURCE_PRIORITY = 90


def should_replace_primary(existing_priority: int | None, incoming_priority: int) -> bool:
    if existing_priority is None:
        return True
    return incoming_priority <= existing_priority
