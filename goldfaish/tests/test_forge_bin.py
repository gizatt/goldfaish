from goldfaish import FORGE_BIN_PATH

def test_forge_bin_exists() -> bool:
    """Check if the Forge binary exists."""
    assert FORGE_BIN_PATH.exists()
