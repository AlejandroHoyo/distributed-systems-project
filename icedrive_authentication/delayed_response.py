"""Servant implementation for the delayed response mechanism."""
from __future__ import annotations
from typing import TYPE_CHECKING

import Ice
import IceDrive

from .user import User

if TYPE_CHECKING:
    from .query_executor import QueryExecutor

class AuthenticationQueryResponse(IceDrive.AuthenticationQueryResponse):
    """Query response receiver."""

    def __init__(self, future: Ice.Future) -> None: 
        """Initialize query response handler"""
        self.future = future

    def loginResponse(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> None:
        """Receive an User when other service instance knows about it and credentials are correct."""
        self.future.set_result(user)

    def userExists(self, username: str, current: Ice.Current = None) -> None:
        """Receive an invocation when other service instance knows the user exists."""
        self.future.set_exception(IceDrive.UserAlreadyExists(username))

    def userRemoved(self, current: Ice.Current = None) -> None:
        """Receive an invocation when other service instance knows the user and removed it."""
        self.future.set_result(None)

    def verifyUserResponse(self, result: bool, current: Ice.Current = None) -> None:
        """Receive a boolean when other service instance is owner of the `user`."""
        self.future.set_result(result)

class AuthenticationQuery(IceDrive.AuthenticationQuery):
    """Query receiver."""

    def __init__(self, query_executor: QueryExecutor):
        self.query_executor = query_executor

    def login(self, username: str, password: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user login."""
        success = self.query_executor.login(username, password)
        if not success:
            return

        user_obj = User(username)
        user_prx = IceDrive.UserPrx.uncheckedCast(current.adapter.addWithUUID(user_obj))
        print("User login query received")
        response.loginResponse(user_prx)

    def doesUserExist(self, username: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user existence."""
        if self.query_executor.user_exists(username):
            print("User existence query received")
            response.userExists(username)

    def removeUser(self, username: str, password: str, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an user to be removed."""
        success = self.query_executor.remove_user(username, password)
        if success:
            print("User remove query received")
            response.userRemoved()

    def verifyUser(self, user: IceDrive.UserPrx, response: IceDrive.AuthenticationQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query about an `User` to be verified."""

        user_object = current.adapter.find(user.ice_getIdentity())
        if user_object is not None:
            print("Verify user query received")
            response.verifyUserResponse(True)