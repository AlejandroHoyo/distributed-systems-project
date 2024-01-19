import time

import Ice
import IceDrive

TWO_MINUTES = 2 * 60

class User(IceDrive.User):
    """Implementation of an IceDrive.User interface."""
    def __init__(self, username: str) -> None:
        self.username = username
        self.creation_timestamp = time.monotonic()

    def getUsername(self, current: Ice.Current = None) -> str:
        """Return the username for the User object."""
        return self.username

    def isAlive(self, current: Ice.Current = None) -> bool:
        """Check if the authentication is still valid or not."""
        
        return time.monotonic() - self.creation_timestamp <= TWO_MINUTES 

    def refresh(self, current: Ice.Current = None) -> None:
        """Renew the authentication for 1 more period of time."""
        if not self.isAlive():
            raise IceDrive.Unauthorized(self.username)
        
        self.creation_timestamp = time.monotonic()