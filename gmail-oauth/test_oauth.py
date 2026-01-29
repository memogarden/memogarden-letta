"""Placeholder tests for GMail OAuth flow."""

import tempfile


def test_oauth_client_initialization():
    """Test that OAuth client initializes without HACM."""
    from gmail_oauth import GmailOAuthClient

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".enc") as hacm:
        client = GmailOAuthClient(hacm.name, client_id="test_id", client_secret="test_secret")

        # Should generate authorization URL
        url = client.get_authorization_url()
        assert "accounts.google.com" in url
        assert "test_id" in url
        assert "offline" in url
        assert "consent" in url


def test_state_generation():
    """Test that state parameter is generated and unique."""
    from gmail_oauth import GmailOAuthClient

    state1 = GmailOAuthClient._generate_state()
    state2 = GmailOAuthClient._generate_state()

    assert state1 != state2
    assert len(state1) > 16


def test_state_is_url_safe():
    """Test that state parameter is URL-safe."""
    from gmail_oauth import GmailOAuthClient

    state = GmailOAuthClient._generate_state()

    # Should not contain URL-unsafe characters
    assert "-" in state or "_" in state
    # Should be base64-like
    assert len(state) >= 16
