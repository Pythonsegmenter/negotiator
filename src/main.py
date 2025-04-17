"""Main entry point for the Negotiator Travel Agent application."""

from src.data_manager import clear_data_dir
from src.user_manager import UserManager


def main() -> None:
    """Initialize and run the main application flow."""

    clear_data_dir()

    # Initialize the user manager
    UserManager()


if __name__ == "__main__":
    main()
