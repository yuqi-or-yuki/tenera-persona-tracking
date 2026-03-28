#!/usr/bin/env bash
# Quickstart example: create personas, add entities, track events, run clustering.
# Prerequisites: server running (`tpt serve`) and TPT_API_KEY set.

set -e
export TPT_API_KEY="${TPT_API_KEY:-your-api-key-here}"

echo "=== Creating personas ==="
tpt persona create alice --name "Alice Chen" \
  -e plan=enterprise -e company_size=500 -e industry=tech -e monthly_spend=2000

tpt persona create bob --name "Bob Martinez" \
  -e plan=free -e company_size=5 -e industry=education -e monthly_spend=0

tpt persona create charlie --name "Charlie Kim" \
  -e plan=pro -e company_size=50 -e industry=tech -e monthly_spend=500

tpt persona create diana --name "Diana Okafor" \
  -e plan=enterprise -e company_size=1000 -e industry=finance -e monthly_spend=5000

tpt persona create eve --name "Eve Larsson" \
  -e plan=free -e company_size=3 -e industry=education -e monthly_spend=0

echo ""
echo "=== Tracking events ==="
tpt track alice page_view -p '{"page": "/dashboard"}'
tpt track alice feature_used -p '{"feature": "cohort_builder"}'
tpt track bob page_view -p '{"page": "/pricing"}'
tpt track bob page_view -p '{"page": "/signup"}'
tpt track charlie plan_upgrade -p '{"from": "free", "to": "pro"}'
tpt track diana plan_upgrade -p '{"from": "pro", "to": "enterprise"}'

echo ""
echo "=== Listing personas ==="
tpt persona list

echo ""
echo "=== Viewing Alice's profile ==="
tpt persona get alice

echo ""
echo "=== Viewing Alice's events ==="
tpt events alice

echo ""
echo "=== Running clustering ==="
tpt cluster run

echo ""
echo "=== Cluster results ==="
tpt cluster results

echo ""
echo "Done! Visit http://localhost:8000 for the dashboard."
