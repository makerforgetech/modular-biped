import json
import paho.mqtt.client as mqtt
from pubsub import pub

class MessagingService:
    def __init__(self, **kwargs):
        self.protocol = kwargs.get('protocol', 'pubsub')
        self.messaging_service = None
        if self.protocol == 'mqtt':
            self.host = kwargs.get('mqtt_host', 'localhost')
            self.port = kwargs.get('port', 1883)
            self.messaging_service = MQTTMessagingService(broker=self.host, port=self.port)
        elif self.protocol == 'pubsub':
            self.messaging_service = PubSubMessagingService()
        else:
            raise ValueError(f"Invalid protocol: {self.protocol}")

    """Base class for messaging services"""
    def subscribe(self, topic, callback, **kwargs):
        raise NotImplementedError
    
    def publish(self, topic, message=None):
        raise NotImplementedError


class PubSubMessagingService(MessagingService):
    def __init__(self):
        self.protocol = 'pubsub'
        print("[PubSubMessagingService] Initialized")
        
    """pypubsub-based messaging implementation"""
    def subscribe(self, topic, callback, **kwargs):
        """
        Subscribe to a topic.
        
        :param topic: Topic string (e.g., 'system/log').
        :param callback: Callback function.
        :param kwargs: Optional keyword arguments.
        
        Example:
        ```
        def callback(message):
            print(message)
            
        messaging_service.subscribe('system/log', callback)
        
        ```
        """
        print(f"[PubSubMessagingService] Subscribing to {topic} to call {callback.__self__.__class__.__name__}.{callback.__name__}")
        pub.subscribe(callback, topic, **kwargs)

    def publish(self, topic, *args, **kwargs):
        """
        Publish a message to a topic.
        
        - If only one argument is provided, send it as-is.
        - If multiple arguments or keyword arguments are provided, send as JSON.

        :param topic: Topic string (e.g., 'system/log').
        :param args: Optional positional arguments.
        :param kwargs: Optional keyword arguments.
        """
            
        if len(args) == 1 and not kwargs:
            pub.sendMessage(topic, message=args[0])
        else:
            # pass kwargs to pubsub
            pub.sendMessage(topic, **kwargs)

class MQTTMessagingService(MessagingService):
    """MQTT-based messaging implementation"""
    def __init__(self, broker="localhost", port=1883):
        self.protocol = 'mqtt'
        print(f"[MQTTMessagingService] Connecting to {broker}:{port}")
        self.client = mqtt.Client()
        # self.client.on_message = self._on_message
        self.client.connect(broker, port, 60)
        self.subscriptions = {}
        self.client.loop_start()
        
    def __del__(self):
        self.client.loop_stop()

    def subscribe(self, topic, callback, **kwargs):
        raise NotImplementedError
    
    def publish(self, topic, message=None):
        raise NotImplementedError
