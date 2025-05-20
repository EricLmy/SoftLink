import os
import sys
import subprocess
import platform
import time

# --- Configuration ---
MIN_PYTHON_VERSION = (3, 8)
REQUIRED_ENV_VARS = {
    'FLASK_APP': 'run.py',  # Adjust if your entry point is different
    'FLASK_ENV': 'development',      # Can be 'development' or 'production'. Default to development.
    'DATABASE_URL': 'sqlite:///./test.db',   # Default to a local SQLite DB for easier dev start
    # Add other critical env vars if any
}
DEV_HOST = '127.0.0.1'
DEV_PORT = 5000
PROD_WORKERS = (os.cpu_count() or 2) * 2 + 1 # Gunicorn's recommended formula, with fallback for os.cpu_count()
PROD_HOST = '0.0.0.0' 
PROD_PORT = 8000 # Common port for Gunicorn, adjust if needed

# --- Helper Functions ---
def print_info(message):
    print(f"[INFO] {message}")

def print_warning(message):
    print(f"[WARNING] {message}")

def print_error(message):
    print(f"[ERROR] {message}")
    sys.exit(1)

def print_success(message):
    print(f"[SUCCESS] {message}")

def check_python_version():
    print_info(f"Current Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if sys.version_info < MIN_PYTHON_VERSION:
        print_error(
            f"Python version {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher is required. "
            f"You are using {sys.version_info.major}.{sys.version_info.minor}."
        )
    print_success("Python version check passed.")

def check_env_variables():
    print_info("Checking required environment variables...")
    missing_vars = []
    for var, default_value in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if value is None:
            if default_value is not None:
                print_warning(f"{var} is not set. Using default value: '{default_value}'. Consider setting it in a .env file.")
                os.environ[var] = default_value
            else:
                missing_vars.append(var)
        else:
            print_info(f"  - {var} is set to: '{value}'")

    if missing_vars:
        print_error(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please set them (e.g., in a .env file and ensure it's loaded, or export them directly)."
        )
    print_success("Environment variable check passed.")

def check_dependencies():
    print_info("Checking core dependencies...")
    try:
        import flask
        import sqlalchemy
        # import psycopg2 # Or your specific DB driver if not covered by sqlalchemy implicitly for check
        # Add other critical imports here
        print_info("  - Flask found.")
        print_info("  - SQLAlchemy found.")
        # print_info("  - DB Driver found.")
    except ImportError as e:
        print_error(
            f"Missing core dependency: {e.name}. "
            f"Please install all required packages by running: pip install -r requirements.txt"
        )
    print_success("Core dependencies check passed.")

def check_database_connection_and_schema(flask_app_path='app'):
    """
    Tries to connect to the database and check for a key table.
    This is a basic check. For full schema validation, migrations (Alembic) are better.
    """
    print_info("Attempting to check database connection and basic schema...")

    flask_app_env = os.getenv('FLASK_APP', REQUIRED_ENV_VARS.get('FLASK_APP'))
    if not flask_app_env:
        print_warning("FLASK_APP is not set, cannot reliably run flask commands for DB check. Skipping detailed DB check.")
        return

    db_url = os.getenv('DATABASE_URL')
    print_info(f"DATABASE_URL is set to: {db_url}")

    if db_url and db_url.startswith('sqlite:///'):
        print_info("SQLite database detected.")
        db_file_path = db_url.replace('sqlite:///', '')
        # Handle absolute paths (starting with / or drive letter like C:) vs relative paths
        if not os.path.isabs(db_file_path):
            # In start_server.py, we changed CWD to script_dir, so this path is relative to script_dir
            db_file_path = os.path.join(os.getcwd(), db_file_path)
        
        db_dir = os.path.dirname(db_file_path)
        try:
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                print_info(f"Created directory for SQLite database: {db_dir}")
            print_info("For SQLite, ensure your Flask app initializes the database correctly (e.g., using SQLAlchemy's db.create_all()).")
            print_info("If using Flask-Migrate with SQLite, the commands (init, migrate, upgrade) are similar.")
            print_info("  1. flask db init (if .migrations folder doesn't exist)")
            print_info("  2. flask db migrate -m \"Initial migration\"")
            print_info("  3. flask db upgrade")
        except Exception as e:
            print_warning(f"Error while preparing SQLite path: {e}. Please check permissions and path.")

    elif db_url: # For other databases like PostgreSQL
        print_warning("Database readiness check is simplified in this script for non-SQLite DBs.")
        print_info("Please ensure your database server is running and accessible.")
        print_info("If using Flask-Migrate, ensure your database is migrated to the latest version:")
        print_info("  1. flask db init (if .migrations folder doesn't exist)")
        print_info("  2. flask db migrate -m \"Initial migration\"")
        print_info("  3. flask db upgrade")
    else:
        print_warning("DATABASE_URL is not set. Database checks will be limited.")

    print_success("Database guidance provided. Please verify manually or through app-specific checks.")


def start_flask_server(host, port):
    print_info(f"Starting Flask development server on http://{host}:{port}...")
    # For Windows, `flask run` is generally fine.
    # For Linux/macOS, also fine but Gunicorn is preferred for anything beyond simple dev.
    # subprocess.run(['flask', 'run', '--host', host, '--port', str(port)], check=True) 
    # Using os.system for simplicity in some cases, but subprocess is better for control.
    cmd = [sys.executable, '-m', 'flask', 'run', '--host', host, '--port', str(port)]
    print_info(f"Executing command: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd)
        process.wait() # Wait for the process to complete (e.g., user stops it)
    except KeyboardInterrupt:
        print_info("Flask server stopped by user.")
        if process:
            process.terminate()
            process.wait()
    except Exception as e:
        print_error(f"Failed to start Flask server: {e}")


def start_gunicorn_server(host, port, workers):
    if platform.system() == "Windows":
        print_warning("Gunicorn is not officially supported on Windows. "
                      "Consider using Waitress or the Flask development server for development on Windows.")
        print_info("Falling back to Flask development server for Windows.")
        start_flask_server(DEV_HOST, DEV_PORT) # Fallback to dev server on Windows
        return

    print_info(f"Starting Gunicorn server on http://{host}:{port} with {workers} workers...")

    gunicorn_app_module_env = os.getenv('FLASK_APP')
    gunicorn_app_module = ''

    if not gunicorn_app_module_env:
        default_flask_app_from_config = REQUIRED_ENV_VARS.get('FLASK_APP')
        if default_flask_app_from_config and default_flask_app_from_config.endswith('.py'):
            gunicorn_app_module = default_flask_app_from_config[:-3] + ':app'
            print_warning(f"FLASK_APP environment variable is not set. Defaulting to '{gunicorn_app_module}' for Gunicorn based on script's REQUIRED_ENV_VARS.")
            print_warning(f"This assumes an Flask app instance named 'app' in '{default_flask_app_from_config}'.")
        elif default_flask_app_from_config: # e.g. 'run:app' or 'myproject:create_app()'
            gunicorn_app_module = default_flask_app_from_config
            print_info(f"FLASK_APP environment variable is not set. Using configured default '{gunicorn_app_module}' from script's REQUIRED_ENV_VARS for Gunicorn.")
        else:
            if os.path.exists('run.py'):
                gunicorn_app_module = 'run:app'
                print_warning(f"FLASK_APP environment variable is not set. Found 'run.py', defaulting to '{gunicorn_app_module}' for Gunicorn.")
                print_warning("This assumes a Flask app instance named 'app' in 'run.py'.")
            elif os.path.exists('app.py'):
                gunicorn_app_module = 'app:app'
                print_warning(f"FLASK_APP environment variable is not set. Found 'app.py', defaulting to '{gunicorn_app_module}' for Gunicorn.")
                print_warning("This assumes a Flask app instance named 'app' in 'app.py'.")
            elif os.path.exists('wsgi.py'):
                gunicorn_app_module = 'wsgi:app'
                print_warning(f"FLASK_APP environment variable is not set. Found 'wsgi.py', defaulting to '{gunicorn_app_module}' for Gunicorn.")
                print_warning("This assumes a Flask app instance named 'app' in 'wsgi.py'.")
            else:
                gunicorn_app_module = 'main:app' # A common fallback
                print_warning(f"FLASK_APP environment variable is not set, and could not infer a specific .py file (run.py, app.py, wsgi.py). Defaulting to '{gunicorn_app_module}'.")
                print_warning("Ensure you have a 'main.py' with a Flask 'app' instance, or set FLASK_APP explicitly.")
    else:
        gunicorn_app_module = gunicorn_app_module_env
        if gunicorn_app_module.endswith('.py'):
            original_setting = gunicorn_app_module
            gunicorn_app_module = original_setting[:-3] + ':app'
            print_warning(f"FLASK_APP is set to '{original_setting}', which looks like a Python file. "
                          f"Attempting to use '{gunicorn_app_module}' for Gunicorn.")
            print_warning(f"Ensure 'app' is the Flask application instance or factory in '{original_setting}'.")
        else:
            print_info(f"Using FLASK_APP='{gunicorn_app_module}' for Gunicorn.")

    cmd = ['gunicorn', '--workers', str(workers), '--bind', f"{host}:{port}", gunicorn_app_module]
    print_info(f"Executing command: {' '.join(cmd)}")

    process = None
    try:
        process = subprocess.Popen(cmd)
        process.wait() # Wait for Gunicorn to exit
    except KeyboardInterrupt:
        print_info("Gunicorn server stopping due to user interrupt (Ctrl+C)...")
        if process:
            print_info("Sending SIGTERM to Gunicorn process...")
            process.terminate() # Send SIGTERM for graceful shutdown
            try:
                process.wait(timeout=10) # Wait for Gunicorn to shutdown gracefully
                print_info("Gunicorn process terminated gracefully.")
            except subprocess.TimeoutExpired:
                print_warning("Gunicorn did not terminate gracefully after 10 seconds. Sending SIGKILL...")
                process.kill() # Force kill if it doesn't terminate
                try:
                    process.wait(timeout=5) # Wait for kill to complete
                    print_info("Gunicorn process killed.")
                except subprocess.TimeoutExpired:
                    print_error("Gunicorn process did not die even after SIGKILL. Manual intervention may be required.")
                except Exception as e_kill_wait: # Catch other exceptions during kill wait
                    print_warning(f"Exception while waiting for Gunicorn process to die after SIGKILL: {e_kill_wait}")
            except Exception as e_term_wait: # Catch other exceptions during terminate wait
                 print_warning(f"Exception while waiting for Gunicorn process to terminate: {e_term_wait}")
        else:
            print_info("Gunicorn process was not started or already stopped.")
    except FileNotFoundError:
        print_error("Gunicorn command not found. Please ensure Gunicorn is installed and in your PATH. "
                    "You can typically install it with: pip install gunicorn")
    except Exception as e:
        print_error(f"Failed to start Gunicorn server: {e}")
    finally:
        if process and process.poll() is None: # Check if process is still running
            print_warning("Gunicorn process is still running in finally block. Attempting to terminate and kill.")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print_warning("Gunicorn (finally block): Did not terminate gracefully, killing.")
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print_error("Gunicorn (finally block): Failed to kill process.")
                except Exception:
                    pass # Ignore further errors on final kill attempt
            except Exception:
                pass # Ignore errors on final terminate attempt
        print_info("Gunicorn server process cleanup finished.")


# --- Main Execution ---
if __name__ == "__main__":
    # Move to the script's directory to ensure relative paths for .env etc., work as expected
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print_info(f"Changed working directory to: {script_dir}")

    # Load environment variables from .env file if it exists
    # This is a simple check; for more robust .env handling, consider python-dotenv library
    if os.path.exists('.env'):
        print_info("Found .env file, attempting to load environment variables...")
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\'"') # Remove potential quotes
                        if key not in os.environ: # Only set if not already set in the environment
                            os.environ[key] = value
                            print_info(f"  Loaded from .env: {key}")
                        else:
                            print_info(f"  Skipped from .env (already set in environment): {key}")
            print_success(".env file processing complete.")
        except Exception as e:
            print_warning(f"Error reading .env file: {e}. Proceeding with existing environment variables.")
    else:
        print_info(".env file not found. Using existing environment variables.")

    check_python_version()
    check_env_variables() # This will now benefit from .env loading if FLASK_ENV was there
    check_dependencies()
    check_database_connection_and_schema()

    flask_env = os.getenv('FLASK_ENV', 'development').lower()
    print_info(f"FLASK_ENV is set to '{flask_env}'.")

    if flask_env == 'production':
        print_info("Production environment detected. Starting Gunicorn server.")
        # Use PROD_HOST, PROD_PORT, PROD_WORKERS which are defined globally
        start_gunicorn_server(PROD_HOST, PROD_PORT, PROD_WORKERS)
    else:
        if flask_env != 'development':
            print_warning(f"FLASK_ENV is '{flask_env}', which is not 'production'. Defaulting to development mode.")
        print_info("Development environment detected. Starting Flask development server.")
        # Use DEV_HOST, DEV_PORT which are defined globally
        start_flask_server(DEV_HOST, DEV_PORT)