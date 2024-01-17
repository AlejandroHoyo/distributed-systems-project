"""Servant implementations for service discovery."""

import random
import Ice
import IceDrive
import time
import logging
from threading import Event, Thread

ANNOUNCE_FREQUENCY = 5


class Announcer:
    def __init__(self, proxy, announcer_publisher):
        self.proxy = proxy
        self.announcer_publisher = announcer_publisher
        self.stop_event = Event()

    def start(self):
        self.thread = Thread(target=self.announce)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
       
    def announce(self):
        while not self.stop_event.is_set():
            self.announcer_publisher.announceAuthentication(self.proxy)
            time.sleep(ANNOUNCE_FREQUENCY)


class Discovery(IceDrive.Discovery):
    """Servants class for service discovery."""

    def __init__(self): 
        self.authentication_services = {}
        self.directory_services = {}
        self.blob_services = {}

    def announceAuthentication(self, prx: IceDrive.AuthenticationPrx, current: Ice.Current = None) -> None:
        """Receive an Authentication service announcement."""
        if prx not in self.authentication_services:
            identifier = prx.ice_getIdentity()
            self.authentication_services[prx] = identifier
            logging.debug("New Authentication service available at %s", prx)

    def announceDirectoryService(self, prx: IceDrive.DirectoryServicePrx, current: Ice.Current = None) -> None:
        """Receive a Directory service announcement."""
        if prx not in self.directory_services:
            identifier = prx.ice_getIdentity()
            self.directory_services[prx] = identifier
            logging.debug("New Directory service available at %s", prx)

    def announceBlobService(self, prx: IceDrive.BlobServicePrx, current: Ice.Current = None) -> None:
        """Receive a Blob service announcement."""
        if prx not in self.blob_services:
            identifier = prx.ice_getIdentity()
            self.blob_services[prx] = identifier
            logging.debug("New Blob service available at %s", prx)

    def get_authentication_service(self):  
        if not self.authentication_services: 
            return None
        while True: 
            service = random.choice(list(self.authentication_services.keys()))
            if self.is_service_alive(service):
                return service
            del self.authentication_services[service]

    def is_service_alive (self, service):
        try: 
            service.ice_ping()
            return True
        except Ice.ConnectionRefusedException: 
            return False
    