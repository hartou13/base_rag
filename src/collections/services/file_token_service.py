"""Short-lived HMAC-signed download tokens: signature over file id, user id and expiry."""
import hashlib
import hmac
import time

from src.rag.services import rag_config as cfg

# Optional single-use: signatures already redeemed, kept in memory until they expire.
# (Per process; use a shared store if the API runs with several workers.)
_used: dict[str, int] = {}


def _mac(file_id: str, user_id: str, exp: int, secret: str | None = None) -> str:
    key = (secret if secret is not None else cfg.FILE_URL_SECRET).encode()
    return hmac.new(key, f"{file_id}|{user_id}|{exp}".encode(), hashlib.sha256).hexdigest()


def sign(file_id: str, user_id: str, ttl: int | None = None, now: float | None = None) -> tuple[str, int, str]:
    """Returns (user_id, exp, signature)."""
    exp = int((now if now is not None else time.time()) + (ttl or cfg.FILE_URL_TTL_SECONDS))
    return user_id, exp, _mac(file_id, user_id, exp)


def verify(file_id: str, user_id: str, exp: int, sig: str, now: float | None = None, single_use: bool | None = None) -> bool:
    current = now if now is not None else time.time()
    if exp < current:
        return False
    if not hmac.compare_digest(_mac(file_id, user_id, exp), sig or ""):
        return False
    if single_use if single_use is not None else cfg.FILE_URL_SINGLE_USE:
        for s, e in list(_used.items()):
            if e < current:
                del _used[s]
        if sig in _used:
            return False
        _used[sig] = exp
    return True
