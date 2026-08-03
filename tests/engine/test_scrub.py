from scrub import scrub


def test_scrubs_key_value_assignments():
    assert "hunter2secret" not in scrub("export API_KEY=hunter2secret && run")
    assert "[REDACTED]" in scrub("DOPPLER_TOKEN=dp.st.abc123def456")


def test_scrubs_known_token_shapes():
    for tok in ["sk-abcdefghijklmnop1234", "ghp_" + "a" * 24, "AKIA" + "A" * 16,
                "xoxb-1234567890-abcdef"]:
        assert tok not in scrub(f"using {tok} here")


def test_scrubs_bearer_and_cli_password_args():
    assert "eyJhbGciOi12345678" not in scrub("Authorization: Bearer eyJhbGciOi12345678")
    assert "s3cr3tpass" not in scrub("mysql --password=s3cr3tpass -u root")


def test_scrubs_userinfo_urls():
    out = scrub("git clone https://user:p4ssw0rd@github.com/x/y.git")
    assert "p4ssw0rd" not in out


def test_scrubs_sensitive_env_values():
    env = {"MY_SECRET_TOKEN": "topsecretvalue99", "PATH": "/usr/bin:/bin", "HOME": "/Users/x"}
    out = scrub("error: auth failed for topsecretvalue99", env=env)
    assert "topsecretvalue99" not in out
    # non-sensitive env vars are NOT redacted (PATH would destroy every log line)
    assert "/usr/bin" in scrub("looked in /usr/bin:/bin", env=env)


def test_short_env_values_ignored():
    env = {"API_KEY": "short"}  # <8 chars — too collision-prone to redact
    assert scrub("short circuit", env=env) == "short circuit"


def test_plain_text_untouched():
    s = "colcon build failed: package 'nav2_bringup' not found"
    assert scrub(s, env={}) == s


def test_does_not_redact_nonsensitive_key_assignments():
    """Pattern 1 should not redact KEY=value for non-sensitive keys."""
    # These should survive unchanged
    assert "ROS_DISTRO=humble" in scrub("ROS_DISTRO=humble", env={})
    assert "AMENT_PREFIX_PATH=/opt/ros/humble" in scrub("AMENT_PREFIX_PATH=/opt/ros/humble", env={})
    assert "PATH=/usr/bin:/bin" in scrub("PATH=/usr/bin:/bin", env={})


def test_does_not_redact_nonsensitive_env_values():
    """Env values should not be redacted if the key is not sensitive."""
    env = {"COMPASS_HEADING": "northnortheast", "KEYBOARD_LAYOUT": "colemak-dh-iso"}
    out = scrub("heading is northnortheast and layout is colemak-dh-iso", env=env)
    assert "northnortheast" in out
    assert "colemak-dh-iso" in out


def test_sensitive_redaction_still_works():
    """Verify sensitive keys are still redacted after gating fix."""
    # Pattern 1: direct assignment with sensitive key
    assert "hunter2secret" not in scrub("API_KEY=hunter2secret", env={})

    # Env value redaction with sensitive key
    env = {"API_KEY": "longsecret99"}
    out = scrub("auth failed: longsecret99", env=env)
    assert "longsecret99" not in out


def test_redacts_credentials_and_authorization_inflections():
    """Credential/authorization inflections (CREDENTIALS, AUTHORIZATION) must be redacted."""
    env = {"GOOGLE_APPLICATION_CREDENTIALS": "eyFakeSvcAcctBlob1234"}
    out = scrub("creds file: eyFakeSvcAcctBlob1234", env=env)
    assert "eyFakeSvcAcctBlob1234" not in out
    assert "[REDACTED]" in out

    env = {"AUTHORIZATION": "Basic abcdef123456"}
    out = scrub("header: Basic abcdef123456", env=env)
    assert "abcdef123456" not in out


def test_false_positive_prevention_persists():
    """COMPASS_HEADING and KEYBOARD_LAYOUT must stay unredacted after credential fix."""
    env = {"COMPASS_HEADING": "northnortheast", "KEYBOARD_LAYOUT": "colemak-dh-iso"}
    out = scrub("heading: northnortheast layout: colemak-dh-iso", env=env)
    assert "northnortheast" in out
    assert "colemak-dh-iso" in out
