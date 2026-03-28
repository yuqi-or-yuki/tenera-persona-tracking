"""Example: Using the REST API directly with httpx (or requests).

This shows how an external service (like Tenera) would integrate.
Start the server first: `tpt serve`
"""

import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def main():
    # 1. Create a persona with entities
    print("Creating persona...")
    resp = httpx.post(
        f"{BASE_URL}/api/v1/personas",
        headers=HEADERS,
        json={
            "distinct_id": "api_user_1",
            "name": "API Test User",
            "entities": [
                {"key": "plan", "value": "pro"},
                {"key": "company", "value": "TestCorp"},
                {"key": "role", "value": "developer"},
            ],
        },
    )
    persona = resp.json()
    print(f"  Created: {persona['distinct_id']} (id={persona['id']})")

    # 2. Track some events
    print("\nTracking events...")
    for event_type, props in [
        ("page_view", {"page": "/docs"}),
        ("api_call", {"endpoint": "/personas", "method": "POST"}),
        ("feature_used", {"feature": "clustering"}),
    ]:
        resp = httpx.post(
            f"{BASE_URL}/api/v1/track",
            headers=HEADERS,
            params={"distinct_id": "api_user_1"},
            json={"event_type": event_type, "properties": props},
        )
        print(f"  Tracked: {event_type}")

    # 3. Update an entity
    print("\nUpdating entity...")
    httpx.post(
        f"{BASE_URL}/api/v1/personas/{persona['id']}/entities",
        headers=HEADERS,
        json=[{"key": "plan", "value": "enterprise"}],
    )
    print("  plan -> enterprise")

    # 4. Get persona with all data
    print("\nFetching persona...")
    resp = httpx.get(f"{BASE_URL}/api/v1/personas/{persona['id']}", headers=HEADERS)
    p = resp.json()
    print(f"  {p['distinct_id']} ({p['name']})")
    for e in p["entities"]:
        print(f"    {e['key']}: {e['value']}")

    # 5. Get event timeline
    print("\nEvent timeline:")
    resp = httpx.get(
        f"{BASE_URL}/api/v1/personas/{persona['id']}/events", headers=HEADERS
    )
    for event in resp.json():
        print(f"  [{event['timestamp'][:19]}] {event['event_type']} {event.get('properties', '')}")

    # 6. Clean up
    print("\nDeleting persona...")
    httpx.delete(f"{BASE_URL}/api/v1/personas/{persona['id']}", headers=HEADERS)
    print("  Done.")


if __name__ == "__main__":
    main()
