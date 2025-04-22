"""Integration test for the main entry point of the application."""

from src.main import main


def test_main_runs_without_errors():
    """
    Test that the main function runs without errors.

    This integration test verifies that the main application flow can execute
    from start to finish without raising exceptions, using the actual settings
    from settings.toml in the root directory.
    """
    # Simply run the main function and verify it completes without raising exceptions
    main()
