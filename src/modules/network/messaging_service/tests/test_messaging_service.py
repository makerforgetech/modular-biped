import sys
import unittest
from unittest.mock import MagicMock, patch, call

mock_paho = MagicMock()
mock_pubsub = MagicMock()
sys.modules['paho'] = mock_paho
sys.modules['paho.mqtt'] = mock_paho.mqtt
sys.modules['paho.mqtt.client'] = mock_paho.mqtt.client
sys.modules['pubsub'] = mock_pubsub
sys.modules['pubsub.pub'] = mock_pubsub.pub

from modules.network.messaging_service.messaging_service import (
    MessagingService,
    PubSubMessagingService,
    MQTTMessagingService,
)


class TestMessagingServiceInit(unittest.TestCase):

    def test_init_pubsub(self):
        ms = MessagingService(protocol='pubsub')
        self.assertEqual(ms.protocol, 'pubsub')
        self.assertIsInstance(ms._pubsub, PubSubMessagingService)
        self.assertIsNone(ms._mqtt)

    def test_init_mqtt(self):
        ms = MessagingService(protocol='mqtt', mqtt_host='localhost', mqtt_port=1883)
        self.assertEqual(ms.protocol, 'mqtt')
        self.assertIsNone(ms._pubsub)
        self.assertIsInstance(ms._mqtt, MQTTMessagingService)

    def test_init_both(self):
        ms = MessagingService(protocol='both', mqtt_host='localhost', mqtt_port=1883)
        self.assertEqual(ms.protocol, 'both')
        self.assertIsInstance(ms._pubsub, PubSubMessagingService)
        self.assertIsInstance(ms._mqtt, MQTTMessagingService)

    def test_init_invalid_protocol(self):
        with self.assertRaises(ValueError) as ctx:
            MessagingService(protocol='invalid')
        self.assertIn('invalid', str(ctx.exception))


class TestMessagingServicePubSub(unittest.TestCase):

    def setUp(self):
        self.ms = MessagingService(protocol='pubsub')

    def test_subscribe_delegates_to_pubsub(self):
        with patch.object(self.ms._pubsub, 'subscribe') as mock_sub:
            cb = MagicMock()
            self.ms.subscribe('test/topic', cb)
            mock_sub.assert_called_once_with('test/topic', cb)

    def test_publish_delegates_to_pubsub(self):
        with patch.object(self.ms._pubsub, 'publish') as mock_pub:
            self.ms.publish('test/topic', message='hello')
            mock_pub.assert_called_once_with('test/topic', message='hello')

    def test_publish_mqtt_is_noop_when_no_mqtt(self):
        # Should not raise even when MQTT is not configured
        self.ms.publish_mqtt('test/topic', message='hello')


class TestMessagingServiceBoth(unittest.TestCase):

    def setUp(self):
        self.ms = MessagingService(protocol='both', mqtt_host='localhost', mqtt_port=1883)

    def test_subscribe_calls_both_backends(self):
        with patch.object(self.ms._pubsub, 'subscribe') as mock_ps_sub, \
             patch.object(self.ms._mqtt, 'subscribe') as mock_mqtt_sub:
            cb = MagicMock()
            self.ms.subscribe('test/topic', cb)
            mock_ps_sub.assert_called_once_with('test/topic', cb)
            mock_mqtt_sub.assert_called_once_with('test/topic', cb)

    def test_publish_uses_pubsub_when_both_available(self):
        with patch.object(self.ms._pubsub, 'publish') as mock_ps_pub, \
             patch.object(self.ms._mqtt, 'publish') as mock_mqtt_pub:
            self.ms.publish('test/topic', message='hello')
            mock_ps_pub.assert_called_once_with('test/topic', message='hello')
            mock_mqtt_pub.assert_not_called()

    def test_publish_mqtt_only_calls_mqtt(self):
        with patch.object(self.ms._pubsub, 'publish') as mock_ps_pub, \
             patch.object(self.ms._mqtt, 'publish') as mock_mqtt_pub:
            self.ms.publish_mqtt('test/topic', message='hello')
            mock_ps_pub.assert_not_called()
            mock_mqtt_pub.assert_called_once_with('test/topic', message='hello')


class TestPubSubMessagingService(unittest.TestCase):

    def test_subscribe_and_publish(self):
        ms = PubSubMessagingService()
        callback = MagicMock()
        ms.subscribe('test/topic', callback)
        ms.publish('test/topic', message='hello')


class TestMQTTMessagingService(unittest.TestCase):

    def test_publish_single_arg(self):
        ms = MQTTMessagingService(broker='localhost', port=1883)
        ms.publish('test/topic', 'payload')
        ms.client.publish.assert_called()

    def test_publish_kwargs(self):
        ms = MQTTMessagingService(broker='localhost', port=1883)
        ms.publish('test/topic', key='value')
        ms.client.publish.assert_called()

    def test_subscribe(self):
        ms = MQTTMessagingService(broker='localhost', port=1883)
        cb = MagicMock()
        ms.subscribe('test/topic', cb)
        ms.client.subscribe.assert_called()


if __name__ == '__main__':
    unittest.main()
