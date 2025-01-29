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
        print("PubSubMessagingService: Initialized")
        
    """pypubsub-based messaging implementation"""
    def subscribe(self, topic, callback, **kwargs):
        print(f"PubSubMessagingService: Subscribing to {topic}")
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
        print(f"MQTTMessagingService: Connecting to {broker}:{port}")
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.client.connect(broker, port, 60)
        self.subscriptions = {}
        self.loop_start()
        
    def __del__(self):
        self.loop_stop()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        if topic in self.subscriptions:
            if payload == '':
                self.subscriptions[topic]()
            else:
                self.subscriptions[topic](payload)

    def subscribe(self, topic, callback, **kwargs):
        self.subscriptions[topic] = callback
        self.client.subscribe(topic) # @todo add **kwargs support

    def publish(self, topic, *args, **kwargs):
        """
        Publish a message to a topic.
        
        - If only one argument is provided, send it as-is.
        - If multiple arguments or keyword arguments are provided, send as JSON.

        :param topic: Topic string (e.g., 'system/log').
        :param args: Optional positional arguments.
        :param kwargs: Optional keyword arguments.
        """
        message = None
        if len(args) == 1 and not kwargs:
            # Single argument, send directly
            message = args[0]
        elif args or kwargs:
            # Convert multiple arguments into a JSON object
            message_data = {"args": args} if args else {}
            message_data.update(kwargs)
            message = json.dumps(message_data)

        # Publish the message if present or just the topic
        if message is not None:
            self.client.publish(topic, message)
        else:
            self.client.publish(topic)
            
    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()
