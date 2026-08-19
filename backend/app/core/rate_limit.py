"""
Shared slowapi Limiter instance.

Lives in its own module (rather than app/main.py) so both main.py and any
router module (e.g. chat.py) can import the same limiter without a circular
import between them.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
