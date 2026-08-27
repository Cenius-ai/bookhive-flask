#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies..."
pip install -r requirements.txt

# Generate a random SECRET_KEY if not already set in .env
if [ ! -f .env ]; then
    echo "==> Generating .env with random SECRET_KEY..."
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
    echo "BOOKHIVE_ALLOW_SEED=true" >> .env
else
    if ! grep -q '^SECRET_KEY=' .env 2>/dev/null; then
        echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env
    fi
    if ! grep -q '^BOOKHIVE_ALLOW_SEED=' .env 2>/dev/null; then
        echo "BOOKHIVE_ALLOW_SEED=true" >> .env
    fi
fi

echo "==> Seeding database..."
# Load .env so BOOKHIVE_ALLOW_SEED is set for the seed call
export $(grep -v '^#' .env | xargs)
python3 -c "
from app import create_app
from seed import run_seed
app = create_app()
with app.app_context():
    seeded = run_seed()
    print('Database seeded.' if seeded else 'Database already seeded — skipping.')
"

# Remove the seed gate so the endpoint is locked down at runtime
if grep -q '^BOOKHIVE_ALLOW_SEED=true' .env 2>/dev/null; then
    sed -i '/^BOOKHIVE_ALLOW_SEED=/d' .env
fi

echo ""
echo "==> Setup complete!"
echo "    Start the server with:  flask run --host 0.0.0.0 --port 5000"
echo "    Demo admin: admin@bookhive.com / admin123"
echo ""
