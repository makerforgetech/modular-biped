import inspect
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
        
    def log(self, message, level='info'):
        """
        Advanced logging, includes class name, method name, and line number to message string
        """
        # get class name, method name
        class_name = self.__class__.__name__
        method_name = inspect.stack()[1].function
        
        #get line number of calling class
        frame = inspect.stack()[1]

        message = f"[{class_name}.{method_name}:{frame.lineno}] {str(message)}"
        self.publish(f'log/{level}', message=message)