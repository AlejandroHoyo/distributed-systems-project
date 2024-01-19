"""Authentication service application."""

from __future__ import annotations

import logging
import sys
from typing import List
import IceStorm

import Ice
import IceDrive
import IcePy

from .authentication import Authentication
from .delayed_response import AuthenticationQuery
from .discovery import Discovery, Announcer
from .query_executor import QueryExecutor

class AuthenticationApp(Ice.Application):
    """Implementation of the Ice.Application for the Authentication service."""

    def run(self, args: List[str]) -> int:
        """Execute the code for the AuthentacionApp class."""
        adapter = self.communicator().createObjectAdapter("AuthenticationAdapter")
        adapter.activate()

        # Get discovery proxy
        discovery_servant = Discovery()
        discovery_proxy = adapter.addWithUUID(discovery_servant)

        # Get topic for discovery
        properties = self.communicator().getProperties()
        topic_discovery_name = properties.getProperty("DiscoveryTopic")
        topic_discovery = self.get_topic(topic_discovery_name)

        # Get topic for query authentication
        topic_authentication_query_name = properties.getProperty("AuthenticationQueryTopic")
        topic_authentication_query = self.get_topic(topic_authentication_query_name)
        authentication_query_publisher = self.get_publisher(topic_authentication_query, IceDrive.AuthenticationQuery)

        # Subscribe discovery topic
        self.subscribe_to(topic_discovery, discovery_proxy)
        announcer_publisher = self.get_publisher(topic_discovery, IceDrive.Discovery)

        # Get authenticator and query_receiver proxies
        query_executor = QueryExecutor("users.db")
        authenticator = Authentication(query_executor, authentication_query_publisher)
        query_receiver = AuthenticationQuery(query_executor)
        authenticator_proxy = IceDrive.AuthenticationPrx.uncheckedCast(adapter.addWithUUID(authenticator))
        query_receiver_proxy = IceDrive.AuthenticationQueryPrx.uncheckedCast(adapter.addWithUUID(query_receiver))
       

        # Subscribe query_receiver topic
        self.subscribe_to(topic_authentication_query, query_receiver_proxy)
        logging.info("Authentication service available at: %s", authenticator_proxy)
    
        # Start the announcer
        announcer = Announcer(authenticator_proxy, announcer_publisher)
        announcer.start()

        
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        announcer.stop()

        topic_discovery.unsubscribe(discovery_proxy)

        return 0
        
    def get_topic(self, topic_name: str) -> IceStorm.TopicPrx:
        """ Retrieves the IceStorm topic for the discovery if it exists; 
        if not found, creates it """

        topic_mgr_proxy = IceStorm.TopicManagerPrx.checkedCast(
            self.communicator().propertyToProxy("IceStorm.TopicManager.Proxy"),
        )
        try:
            topic = topic_mgr_proxy.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_mgr_proxy.retrieve(topic_name)
        return topic
    
    def get_publisher(self, topic: IceStorm.TopicPrx, klass: str) -> IcePy.ObjectPrx:
        """ Returns a publisher for the given topic of type 'klass' """
        publisher = topic.getPublisher()
        publisher = getattr(
            IceDrive, f"{klass.__name__}Prx").uncheckedCast(publisher)
        if not publisher:
            raise RuntimeError("Invalid publisher proxy")
        return publisher

    def subscribe_to(self, topic: IceStorm.TopicPrx, proxy: IcePy.ObjectPrx) -> None:
        """ Subscribe 'proxy' to the given topic."""
        topic.subscribeAndGetPublisher({}, proxy)

def main():
    """Handle the icedrive-authentication program."""
    app = AuthenticationApp()
    return app.main(sys.argv)
