import re

class LinterConfig:
    """
    A centralized configuration class for linter settings.
    """

    HARDCODED_SECRET_PATTERN = re.compile(
    # Pattern 1: AWS Key
    r'(?:AKIA[0-9A-Z]{16})'
    r'|'
    # Pattern 2: GitHub Token
    r'(?:ghp_[0-9a-zA-Z]{36})'
    r'|'
    # Pattern 3: JWT Token (handles optional "Bearer ")
    r'(?:(?:Bearer\s+)?ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*)'
    r'|'
    # Pattern 4: User:Pass format
    r'(?:[a-zA-Z0-9\-_]+:[a-zA-Z0-9\-_!@#$%^&*()+=]{8,})'
    r'|'
    # Pattern 5: Generic key=value format
    # Note: This one has an inner group to capture just the value, but the outer group ensures the full match is correct.
    r'(?:(key|secret|token|password|passwd|pwd|credentials?)\s*[:=]\s*[\'"]?([^\s\'"]{8,})[\'"]?)',
    re.IGNORECASE
    )

    
    SUSPICIOUS_KEY_KEYWORDS = [
        "secret", "token", "password", "passwd", "pwd", "credentials", "api_key", "apikey"
    ]