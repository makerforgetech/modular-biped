import json
import paho.mqtt.client as mqtt
from pubsub import pub

VALID_PROTOCOLS = ('pubsub', 'mqtt', 'both')

class MessagingService:
    """
    Unified messaging façade that supports pypubsub, MQTT, or both.

    Config options (via config.yml or environment override):
      protocol: pubsub   # in-process pypubsub only (default)
      protocol: mqtt     # MQTT broker only
      protocol: both     # pypubsub + MQTT available simultaneously
      mqtt_host: localhost
      mqtt_port: 1883

    Routing:
      subscribe()     — registers the callback on ALL active backends so it
                        receives messages from either path.
      publish()       — sends via the *primary* backend only:
                          pubsub / both → pypubsub
                          mqtt          → MQTT
      publish_mqtt()  — sends to the MQTT backend only (no-op when MQTT is
                        not active).  Use this when you need to push data to
                        an external broker without also triggering local
                        pypubsub listeners.
    """

    def __init__(self, **kwargs):
        self.protocol = kwargs.get('protocol', 'pubsub')
        if self.protocol not in VALID_PROTOCOLS:
            raise ValueError(
                f"Invalid protocol '{self.protocol}'. "
                f"Must be one of: {', '.join(VALID_PROTOCOLS)}"
            )
        self._pubsub = None
        self._mqtt = None

        if self.protocol in ('pubsub', 'both'):
            self._pubsub = PubSubMessagingService()

        if self.protocol in ('mqtt', 'both'):
            host = kwargs.get('mqtt_host', 'localhost')
            try:
                port = int(kwargs.get('mqtt_port', 1883))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid mqtt_port '{kwargs.get('mqtt_port')}': must be an integer."
                ) from exc
            self._mqtt = MQTTMessagingService(broker=host, port=port)

    def subscribe(self, topic, callback, **kwargs):
        """
        Subscribe to a topic on all active messaging backends.

        When ``protocol`` is ``both``, the callback is registered on both
        backends so it receives messages published via either path.
        """
        if self._pubsub:
            self._pubsub.subscribe(topic, callback, **kwargs)
        if self._mqtt:
            self._mqtt.subscribe(topic, callback, **kwargs)

    def publish(self, topic, *args, **kwargs):
        """
        Publish a message via the primary backend.

        - ``pubsub`` (default) and ``both`` → publishes to pypubsub only.
        - ``mqtt`` → publishes to MQTT only.

        Use :meth:`publish_mqtt` to target the MQTT backend explicitly when
        ``protocol`` is ``both``.
        """
        if self._pubsub:
            self._pubsub.publish(topic, *args, **kwargs)
        elif self._mqtt:
            self._mqtt.publish(topic, *args, **kwargs)

    def publish_mqtt(self, topic, *args, **kwargs):
        """Publish only to the MQTT backend (no-op if MQTT is not active)."""
        if self._mqtt:
            self._mqtt.publish(topic, *args, **kwargs)


class PubSubMessagingService:
    """pypubsub-based messaging implementation."""

    def __init__(self):
        self.protocol = 'pubsub'
        print("[PubSubMessagingService] Initialized")

    def subscribe(self, topic, callback, **kwargs):
        """
        Subscribe to a topic.

        :param topic: Topic string (e.g., 'system/log').
        :param callback: Callback function.

        Example::

            def on_message(message):
                print(message)

            messaging_service.subscribe('system/log', on_message)
        """
        if hasattr(callback, '__self__') and hasattr(callback, '__name__'):
            cb_name = f"{callback.__self__.__class__.__name__}.{callback.__name__}"
        else:
            cb_name = getattr(callback, '__name__', repr(callback))
        print(f"[PubSubMessagingService] Subscribing to {topic} to call {cb_name}")
        pub.subscribe(callback, topic, **kwargs)

    def publish(self, topic, *args, **kwargs):
        """
        Publish a message to a topic.

        - Single positional argument → sent as the ``message`` keyword.
        - Keyword arguments → forwarded directly to pypubsub.
        """
        if len(args) == 1 and not kwargs:
            pub.sendMessage(topic, message=args[0])
        else:
            pub.sendMessage(topic, **kwargs)


class MQTTMessagingService:
    """MQTT-based messaging implementation."""

    def __init__(self, broker="localhost", port=1883):
        self.protocol = 'mqtt'
        print(f"[MQTTMessagingService] Connecting to {broker}:{port}")
        self.client = mqtt.Client()
        self.client.connect(broker, port, 60)
        self.subscriptions = {}
        self.client.loop_start()

    def __del__(self):
        try:
            self.client.loop_stop()
        except Exception:
            pass

    def subscribe(self, topic, callback, **kwargs):
        """Subscribe to an MQTT topic and call the callback on each message."""
        def on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode('utf-8')
                try:
                    data = json.loads(payload)
                except Exception:
                    data = payload
                if isinstance(data, dict):
                    callback(**data)
                else:
                    callback(data)
            except Exception as e:
                print(f"[MQTTMessagingService] Error in on_message: {e}")

        qos = kwargs.get('qos', 1)
        self.client.subscribe(topic, qos=qos)
        self.client.message_callback_add(topic, on_message)
        print(f"[MQTTMessagingService] Subscribed to topic: {topic}")

    def publish(self, topic, *args, **kwargs):
        """
        Publish a message to an MQTT topic.

        - Single positional argument → sent as a raw string/bytes payload.
        - Keyword arguments → serialised as JSON.
        """
        qos = kwargs.pop('qos', 1)
        if len(args) == 1 and not kwargs:
            payload = args[0]
            if isinstance(payload, bytes):
                pass  # send raw bytes as-is
            elif not isinstance(payload, str):
                payload = json.dumps(payload)
            self.client.publish(topic, payload, qos=qos)
        else:
            self.client.publish(topic, json.dumps(kwargs), qos=qos)
