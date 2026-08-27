# INSTALL

## 1. Prerequisites

- Python 3.11 or later
- `pip` (bundled with Python)

## 2. Get the Code

Clone or download the repository to your local machine.

```bash
git clone <repository-url> bookhive
cd bookhive
```

## 3. Install Dependencies

Create a virtual environment and install the required packages.

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Configure Environment

Copy the example environment file and set a secret key.

```bash
cp .env.example .env
```

Edit `.env` and provide a strong value for `SECRET_KEY` (e.g., a random string). Optionally set `FLASK_DEBUG=1` for development and `BOOKHIVE_ALLOW_SEED=1` to pre‑populate the database with demo books on first launch.

## 5. Run the Application

Start the Flask development server.

```bash
flask --app app run --debug
```

The application will be available at `http://127.0.0.1:5000`.

If you set `FLASK_DEBUG=1` in the environment, the server reloads automatically on code changes.

## 6. Troubleshooting

- **Port 5000 already in use**: Change the port with `flask --app app run --port 8080`.
- **Missing `SECRET_KEY`**: The app will not start. Set it in `.env`.
- **Module not found errors**: Ensure the virtual environment is activated and `pip install -r requirements.txt` completed successfully.
- **SQLite operational error**: Check that the directory where `bookhive.db` is created is writable.