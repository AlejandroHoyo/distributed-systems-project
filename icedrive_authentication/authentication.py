#!/usr/bin/ env python3

"""Module for servants implementations."""
from __future__ import annotations
from typing import TYPE_CHECKING
import Ice
import IceDrive
import threading

from .delayed_response import AuthenticationQueryResponse 
from .user import User

if TYPE_CHECKING:
    from .query_executor import QueryExecutor


WAIT_TIME = 5

class Response:
    def __init__(self, future: Ice.Future, query_prx: IceDrive.AuthenticationQueryResponsePrx) -> None:
        self.future = future
        self.query_prx = query_prx

    @classmethod
    def from_adapter(cls, adapter: Ice.ObjectAdapter) -> Response:
        future = Ice.Future()
        response = AuthenticationQueryResponse(future)
        prx = adapter.addWithUUID(response)
        query_response_prx = IceDrive.AuthenticationQueryResponsePrx.uncheckedCast(prx)
        return cls(future, query_response_prx)
    
    def delete_from_adapter_after(self, adapter: Ice.ObjectAdapter, time: int, exc: IceDrive.Exception = None) -> None:
        threading.Timer(time, self._clean, (adapter, exc)).start()

    def _clean(self, adapter: Ice.ObjectAdapter, exc : IceDrive.Exception | None) -> None:
        adapter.remove(self.query_prx.ice_getIdentity())

        if not self.future.done() and exc is not None:
            self.future.set_exception(exc)
        elif exc is None:
            self.future.set_result(False)


class Authentication(IceDrive.Authentication):
    """Implementation of an IceDrive.Authentication interface."""

    def __init__(self, query_executor: QueryExecutor, query_publisher: IceDrive.AuthenticationQueryPrx) -> None:
        self.query_executor = query_executor
        self.query_publisher = query_publisher 
        self.query_executor.create_db_not_exists()
        self.users = {}

    def login(
        self, username: str, password: str, current: Ice.Current = None
    ) -> IceDrive.UserPrx:
        """Authenticate an user by username and password and return its User."""
        
        success = self.query_executor.login(username, password)
        if not success:
            response = Response.from_adapter(current.adapter)
            self.query_publisher.login(username, password, response.query_prx)
            response.delete_from_adapter_after(current.adapter, WAIT_TIME, IceDrive.Unauthorized(username))
            return response.future

        user_obj = User(username)
        user_prx = IceDrive.UserPrx.uncheckedCast(current.adapter.addWithUUID(user_obj))

        user_identity = user_prx.ice_getIdentity()

        if username in self.users: 
            self.users[username].append(user_identity)
        else: 
            self.users[username] = [user_identity]
            
        return user_prx

    async def newUser(
        self, username: str, password: str, current: Ice.Current = None
    ) -> IceDrive.UserPrx:
        """Create an user with username and the given password."""
        success = self.query_executor.user_exists(username)
        if success:
            raise IceDrive.UserAlreadyExists(username)
        
        response = Response.from_adapter(current.adapter)
        self.query_publisher.doesUserExist(username, response.query_prx)
        response.delete_from_adapter_after(current.adapter, WAIT_TIME)

        await response.future
        
        self.query_executor.insert_user(username, password)
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
            response = Response.from_adapter(current.adapter)
            self.query_publisher.removeUser(username, password, response.query_prx)
            response.delete_from_adapter_after(current.adapter, WAIT_TIME, IceDrive.Unauthorized(username))
            return response.future
        
        users_identitites_to_remove = self.users.get(username, [])
        for user_identity in users_identitites_to_remove:
            current.adapter.remove(user_identity)
        
    def verifyUser(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> bool:
        """Check if the user belongs to this service.
        Don't check anything related to its authentication state or anything else.
        """
        user_object = current.adapter.find(user.ice_getIdentity())
        if user_object is None: 
            response = Response.from_adapter(current.adapter)
            self.query_publisher.verifyUser(user, response.query_prx)
            response.delete_from_adapter_after(current.adapter, WAIT_TIME)
            return response.future

        return True



