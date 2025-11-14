def pytest_addoption(parser):
    """Add options to the pytest command line."""
    parser.addoption(
        "--no-crds",
        action="store_true",
        default=False,
        help="Skip tests against crds",
    )
