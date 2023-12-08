#!/usr/bin/ env python3

"""Module for servants implementations."""
import time
import Ice
import IceDrive


from .query_executor import QueryExecutor 

TWO_MINUTES = 15

class User(IceDrive.User):
    """Implementation of an IceDrive.User interface."""
    def __init__(self, username: str) -> None:
        self.username = username
        self.enable = True
        self.creation_timestamp = time.monotonic()
        #self.last_refresh_timestamp = self.creation_timestamp  # Initialize last refresh time

    def getUsername(self, current: Ice.Current = None) -> str:
        """Return the username for the User object."""
        return self.username

    def isAlive(self, current: Ice.Current = None) -> bool:
        """Check if the authentication is still valid or not."""
        
        return time.monotonic() - self.creation_timestamp <= TWO_MINUTES and self.enable

    def refresh(self, current: Ice.Current = None) -> None:
        """Renew the authentication for 1 more period of time."""
        if not self.enable: 
            raise IceDrive.UserNotExist(self.username)
        if not self.isAlive():
            raise IceDrive.Unauthorized(self.username)
        
        self.creation_timestamp = time.monotonic()
        #self.last_refresh_timestamp = self.creation_timestamp  # Update last refresh time


class Authentication(IceDrive.Authentication):
    """Implementation of an IceDrive.Authentication interface."""

    def __init__(self, db_file: str) -> None:
        self.query_executor = QueryExecutor(db_file)
        self.query_executor.create_db_not_exists()
        self.users = {}

    def login(
        self, username: str, password: str, current: Ice.Current = None
    ) -> IceDrive.UserPrx:

        """Authenticate an user by username and password and return its User."""
        success = self.query_executor.login(username, password)
        if not success:
            raise IceDrive.Unauthorized(username)
        
        user_obj = User(username)
        user_prx = IceDrive.UserPrx.uncheckedCast(current.adapter.addWithUUID(user_obj))
        if username in self.users: 
            self.users[username].append(user_obj)
        else: 
            self.users[username] = [user_obj]

        #print("id", ",".join([str(id(user)) for user in self.users[username]]))
        return user_prx

    def newUser(
        self, username: str, password: str, current: Ice.Current = None
    ) -> IceDrive.UserPrx:
        """Create an user with username and the given password."""
        success = self.query_executor.insert_user(username, password)
        if not success:
            raise IceDrive.UserAlreadyExists(username)
        
        user_obj = User(username)
        user_prx = IceDrive.UserPrx.uncheckedCast(current.adapter.addWithUUID(user_obj))

        self.users[username] = [user_obj]
        return user_prx

    def removeUser(
        self, username: str, password: str, current: Ice.Current = None
    ) -> None:
        """Remove the user "username" if the "password" is correct."""
        success = self.query_executor.remove_user(username, password)
        if not success: 
            raise IceDrive.Unauthorized(username)
        for users in self.users.values():
            for user in users:
                user.enable = False
        del self.users[username]

    def verifyUser(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> bool:
        """Check if the user belongs to this service.
        Don't check anything related to its authentication state or anything else.
        """
        adapter = current.adapter if current else None
        if adapter is None:
            return False
        user_object = adapter.find(user.ice_getIdentity())
        return user_object is not None
