"""Activation helper for network_block_plugin.

Copy the line below into any conftest.py to enforce network blocking for
all tests in that directory and its subdirectories:

    pytest_plugins = ["unified_trading_pm.scripts.dev.network_block_plugin"]

Then run your test suite with:

    pytest --block-network

Or combine with other flags for a full credential-free CI run:

    CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest -m "not sandbox" --block-network

Individual tests that legitimately need network access (e.g. connecting to a
local emulator) can opt out with the @pytest.mark.allow_network marker:

    @pytest.mark.allow_network
    def test_pubsub_emulator() -> None:
        ...  # connects to PUBSUB_EMULATOR_HOST, not a real API

See network_block_plugin.py for full documentation.
"""

# Uncomment and paste into your project's conftest.py to activate globally:
# pytest_plugins = ["unified_trading_pm.scripts.dev.network_block_plugin"]
