
#!/usr/bin/ env python3

"""Module for servants implementations."""
import time
import Ice
import IceDrive

from .query_executor import QueryExecutor 

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

# class Sirviente(Clase.Slice):

#     def __init__(self, instancia_descubridora_de_servicios):
#         self.servicios = instancia_descubridora_de_servicios

#     def metodoSirviente(self, , current=None):
#         dir_proxy = self.servicios.obtenerProxyDirectorio()
        

class Authentication(IceDrive.Authentication):
    """Implementation of an IceDrive.Authentication interface."""

    def __init__(self, db_file: str, query_publisher) -> None:
        self.query_executor = QueryExecutor(db_file)
        self.query_publisher = query_publisher 
        self.query_executor.create_db_not_exists()
        self.users = {}
        
    def prepare_amd_response_callback(self, current: Ice.Current): 
        pass

    def login(
        self, username: str, password: str, current: Ice.Current = None
    ) -> IceDrive.UserPrx:

        """Authenticate an user by username and password and return its User."""
        success = self.query_executor.login(username, password)
        if not success:
            raise IceDrive.Unauthorized(username)
        
       # authenticator_prx = self.authentication_services.get_authentication_service()

        user_obj = User(username)
        user_prx = IceDrive.UserPrx.uncheckedCast(current.adapter.addWithUUID(user_obj))

        user_identity = user_prx.ice_getIdentity()

        if username in self.users: 
            self.users[username].append(user_identity)
        else: 
            self.users[username] = [user_identity]
            
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
        user_identity = user_prx.ice_getIdentity()

        self.users[username] = [user_identity]
        return user_prx

    def removeUser(
        self, username: str, password: str, current: Ice.Current = None
    ) -> None:
        """Remove the user "username" if the "password" is correct."""
        success = self.query_executor.remove_user(username, password)
        if not success: 
            raise IceDrive.Unauthorized(username)
        
        users_identitites_to_remove = self.users.get(username, [])
        for user_identity in users_identitites_to_remove:
            current.adapter.remove(user_identity)
        

    def verifyUser(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> bool:
        """Check if the user belongs to this service.
        Don't check anything related to its authentication state or anything else.
        """
        user_object = current.adapter.find(user.ice_getIdentity())
        return user_object is not None

    def existsUser(self, user: str): 
        success = self.query_executor.user_exists(user)
        return success


