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


def test_scrubs_complete_private_key_pem_blocks():
    for label in ("PRIVATE KEY", "RSA PRIVATE KEY", "EC PRIVATE KEY",
                  "OPENSSH PRIVATE KEY", "ENCRYPTED PRIVATE KEY"):
        secret = "c2VjcmV0LWtleS1tYXRlcmlhbC0xMjM0NTY3ODkw"
        pem = (f"-----BEGIN {label}-----\r\n{secret}\r\n"
               f"-----END {label}-----")
        out = scrub(f"before\n{pem}\nafter", env={})
        assert secret not in out
        assert "BEGIN" not in out
        assert out == "before\n[REDACTED]\nafter"


def test_scrubs_unterminated_private_key_block_to_end_of_text():
    secret = "unterminated-private-key-material-1234567890"
    out = scrub(f"prefix -----BEGIN PRIVATE KEY-----\n{secret}", env={})
    assert out == "prefix [REDACTED]"
    assert secret not in out


def test_private_key_scrub_does_not_match_public_material():
    public_key = "-----BEGIN PUBLIC KEY-----\nordinary-public-material\n-----END PUBLIC KEY-----"
    certificate = "-----BEGIN CERTIFICATE-----\nordinary-certificate\n-----END CERTIFICATE-----"
    text = f"{public_key}\n{certificate}\n" + "x" * 40
    assert scrub(text, env={}) == text


def test_scrubs_long_lines_from_sensitive_multiline_env_values():
    first = "first-sensitive-fragment-1234567890"
    second = "second-sensitive-fragment-0987654321"
    env = {"GCP_SA_KEY": f"metadata\n  {first}  \n{second}\nshort"}

    out = scrub(f"failure exposed {first} only", env=env)
    assert first not in out
    assert "[REDACTED]" in out

    out = scrub(f"failure exposed {second} only", env=env)
    assert second not in out
    assert "[REDACTED]" in out


def test_multiline_env_redaction_preserves_short_and_nonsensitive_lines():
    long_line = "ordinary-long-line-that-is-not-a-secret"
    sensitive = {"API_SECRET": f"short\n{long_line}"}
    nonsensitive = {"ROBOT_CONFIG": f"short\n{long_line}"}

    assert scrub("short", env=sensitive) == "short"
    assert long_line not in scrub(long_line, env=sensitive)
    assert scrub(long_line, env=nonsensitive) == long_line


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
