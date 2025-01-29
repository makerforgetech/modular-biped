class BaseModule:
    
    @property
    def messaging_service(self):
        """Getter for messaging service."""
        return self._messaging_service

    @messaging_service.setter
    def messaging_service(self, service):
        """Setter for messaging service, ensures setup is called."""
        self._messaging_service = service
        self.setup_messaging()

    def setup_messaging(self):
        """Override this method in child classes to subscribe to topics."""
        pass  # No default implementation, subclasses should define their own subscriptions
    
    def publish(self, topic, *args, **kwargs):
        if self.messaging_service is None:
            raise ValueError("Messaging service not set.")
        self.messaging_service.publish(topic, *args, **kwargs)
        
    def subscribe(self, topic, callback, **kwargs):
        if self.messaging_service is None:
            raise ValueError("Messaging service not set.")
        self.messaging_service.subscribe(topic, callback, **kwargs)