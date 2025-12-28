# carpool
carpool app
# Carpool

Simple carpool web application built with Flask.

## Description

This repository contains a small carpooling web app allowing users to register, login, post rides as drivers, search for rides, and book seats. It uses SQLite for storage and Flask for the web server. The app is primarily a learning/demo project and includes static HTML/CSS/JS files and Jinja2 templates in the src/ directory.

## Features

- User registration and login (passwords hashed using Werkzeug)
- Drivers can post rides (car name, start/end location, date, seats, price)
- Users can search for rides and book available seats
- Basic booking concurrency protection using SQLite transactions
- Simple dashboard and pages for viewing bookings and posted rides

## Project structure

- src/
  - app.py             # Main Flask application
  - carpool.db         # SQLite database (created/used at runtime)
  - requirements.txt   # Python dependencies
  - templates/         # Jinja2 HTML templates
  - static/            # CSS, JS, images

## Tech stack

- Python 3.8+
- Flask
- SQLite
- HTML, CSS, JavaScript

## Prerequisites

- Python 3.8 or later
- pip

## Setup (local development)

1. Clone the repository:

   ```bash
   git clone https://github.com/Avnish2002/carpool.git
   cd carpool
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   # macOS / Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   pip install -r src/requirements.txt
   ```

3. (Optional) Set a SECRET_KEY environment variable for session security. If not set, the app will create a random key on each start (not recommended for production):

   ```bash
   # macOS / Linux
   export SECRET_KEY="your_secret_here"
   # Windows (PowerShell)
   setx SECRET_KEY "your_secret_here"
   ```

4. Run the app:

   ```bash
   python src/app.py
   ```

   By default the app starts in debug mode and listens on http://127.0.0.1:5000/

## Notes / Important details

- Database: The app uses an SQLite database file at `src/carpool.db`. The database and required tables are created automatically when the app first runs (see `init_db` in `src/app.py`).

- Environment: For production use, set a persistent `SECRET_KEY` and disable debug mode.

- SQL query note: The search query in `src/app.py` uses both `OR` and `AND`; to ensure correct operator precedence consider adding parentheses in the WHERE clause so the seats condition always applies, e.g.:
  
  ```sql
  WHERE (start_location LIKE ? OR end_location LIKE ?) AND seats > 0
  ```

- Security: Passwords are hashed with Werkzeug. This project is a demo and not hardened for production. Do not use it as-is for a public-facing service without reviewing security, input validation, CSRF protection, and other best practices.

## How to contribute

- Open an issue describing the change you want.
- Fork the repo, create a feature branch (`git checkout -b feature/name`), make changes and open a pull request.

## License

This repository does not currently include a license file. If you want one, add a `LICENSE` (for example MIT) and update the README.

## Contact

If you want me to open a pull request with this README update, confirm and I'll create a branch, commit this README, and open a PR for you.