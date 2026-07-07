from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the global SlowAPI rate limiter using remote IP addresses as keys
limiter = Limiter(key_func=get_remote_address)
