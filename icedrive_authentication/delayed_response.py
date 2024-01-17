"""Servant implementation for the delayed response mechanism."""

import Ice
import IceDrive


class AuthenticationQueryResponse(IceDrive.AuthenticationQueryResponse):
    """Query response receiver."""

    def __init__(self, future: Ice.Future) -> None: 
        """Initialize query response handler"""
        self.future_callback = future

    def loginResponse(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> None:
        """Receive an User when other service instance knows about it and credentials are correct."""
        self.future_callback.set_result(user)
        current.adapter.remove(current.id)

    def userExists(self, username: str, current: Ice.Current = None) -> None:
        """Receive an invocation when other service instance knows the user exists."""
        self.future_callback.set_result(username)
        current.adapter.remove(current.id)

    def userRemoved(self, current: Ice.Current = None) -> None:
        """Receive an invocation when other service instance knows the user and removed it."""
        

    def verifyUserResponse(self, result: bool, current: Ice.Current = None) -> None:
        """Receive a boolean when other service instance is owner of the `user`."""
        self.future_callback.set_result(result)
        current.adapter.remove(current.id)


class AuthenticationQuery(IceDrive.AuthenticationQuery):
    """Query receiver."""

    # def __init__(self, authentication):
    #     self.authentication = authentication

    def login(self, username: str, password: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user login."""
        try: 
            user = self.authentication.login(username, password)
            print("Login query received")
            response.loginResponse(user)
        except IceDrive.Unauthorized:
            pass

    def doesUserExist(self, username: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user existence."""
        try: 
            result = self.authentication.user_exists(username)
            print("User existence")
            response.userExists(username)
        except result is False: 
            pass

    def removeUser(self, username: str, password: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user to be removed."""
        try: 
            self.authentication.removeUser(username, password)
            print("Remove user query received")
            response.userRemoved()
        except IceDrive.Unauthorized:
            pass

    def verifyUser(self, user: IceDrive.UserPrx, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an `User` to be verified."""
        try:
            result = self.authentication.verifyUser(user)
            print("Verify user query received")
            response.verifyUserResponse(result)
        except result is False: 
            pass