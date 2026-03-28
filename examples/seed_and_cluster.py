"""Example: Seed a realistic dataset and run clustering.

Creates 20 personas across different segments, then runs K-Means
to discover natural clusters. Start the server first: `tpt serve`
"""

import random

import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Realistic persona templates
SEGMENTS = [
    # Enterprise tech companies
    {"plan": "enterprise", "industry": "tech", "company_size_range": (200, 2000), "spend_range": (1000, 5000)},
    # Small education orgs
    {"plan": "free", "industry": "education", "company_size_range": (1, 20), "spend_range": (0, 0)},
    # Mid-market healthcare
    {"plan": "pro", "industry": "healthcare", "company_size_range": (50, 200), "spend_range": (200, 800)},
    # SMB finance
    {"plan": "pro", "industry": "finance", "company_size_range": (10, 100), "spend_range": (100, 500)},
]

NAMES = [
    "Aisha Patel", "Ben Nakamura", "Carmen Silva", "David Osei",
    "Elena Kozlov", "Felix Andersen", "Grace Mbeki", "Hassan Demir",
    "Isla McGregor", "Jamal Baptiste", "Keiko Tanaka", "Liam O'Brien",
    "Mei-Ling Zhou", "Noah Berger", "Olga Petrov", "Paulo Costa",
    "Quinn Murphy", "Rosa Gutierrez", "Sven Eriksson", "Tanya Volkov",
]


def main():
    print("Seeding 20 personas...")

    for i, name in enumerate(NAMES):
        segment = SEGMENTS[i % len(SEGMENTS)]
        distinct_id = f"user_{i + 1:03d}"
        company_size = random.randint(*segment["company_size_range"])
        spend = random.randint(*segment["spend_range"])

        resp = httpx.post(
            f"{BASE_URL}/api/v1/personas",
            headers=HEADERS,
            json={
                "distinct_id": distinct_id,
                "name": name,
                "entities": [
                    {"key": "plan", "value": segment["plan"]},
                    {"key": "industry", "value": segment["industry"]},
                    {"key": "company_size", "value": str(company_size)},
                    {"key": "monthly_spend", "value": str(spend)},
                ],
            },
        )
        if resp.status_code == 201:
            print(f"  {distinct_id}: {name} ({segment['plan']}/{segment['industry']})")
        elif resp.status_code == 409:
            print(f"  {distinct_id}: already exists, skipping")
        else:
            print(f"  {distinct_id}: error {resp.status_code}")

    # Run clustering
    print("\nRunning K-Means clustering...")
    resp = httpx.post(
        f"{BASE_URL}/api/v1/clusters/run",
        headers=HEADERS,
        json={"algorithm": "kmeans"},
    )
    result = resp.json()
    print(f"  Found {result['num_clusters']} clusters")
    print(f"  Silhouette score: {result['metrics'].get('silhouette_score', 'N/A')}")

    for label, name in sorted(result.get("cluster_names", {}).items(), key=lambda x: int(x[0])):
        print(f"  [{label}] {name}")

    # Show full results
    print("\nFetching detailed results...")
    resp = httpx.get(f"{BASE_URL}/api/v1/clusters/latest", headers=HEADERS)
    data = resp.json()

    clusters = {}
    for a in data.get("assignments", []):
        label = a["cluster_label"]
        if label not in clusters:
            clusters[label] = {"name": a.get("cluster_name", ""), "members": []}
        clusters[label]["members"].append(a)

    for label in sorted(clusters):
        group = clusters[label]
        print(f"\n  {group['name']} ({len(group['members'])} personas):")
        for m in group["members"]:
            print(f"    {m['distinct_id']}  {m.get('persona_name', '')}")

    print(f"\nDone! Visit http://localhost:8000 to see the dashboard.")


if __name__ == "__main__":
    main()
