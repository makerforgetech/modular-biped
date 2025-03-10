import unittest
from unittest import mock
from modules.base_module import BaseModule

class TestBaseModule(unittest.TestCase):

    def setUp(self):
        self.module = BaseModule()
        self.mock_messaging_service = mock.Mock()
        self.module.messaging_service = self.mock_messaging_service

    def test_messaging_service_getter_setter(self):
        self.module.messaging_service = self.mock_messaging_service
        self.assertEqual(self.module.messaging_service, self.mock_messaging_service)

    def test_publish_no_messaging_service(self):
        self.module.messaging_service = None
        with self.assertRaises(ValueError) as context:
            self.module.publish('test/topic')
        self.assertEqual(str(context.exception), "Messaging service not set.")

    def test_publish_with_messaging_service(self):
        self.module.publish('test/topic', arg1='value1')
        self.mock_messaging_service.publish.assert_called_with('test/topic', arg1='value1')

    def test_subscribe_no_messaging_service(self):
        self.module.messaging_service = None
        with self.assertRaises(ValueError) as context:
            self.module.subscribe('test/topic', lambda x: x)
        self.assertEqual(str(context.exception), "Messaging service not set.")

    def test_subscribe_with_messaging_service(self):
        callback = lambda x: x
        self.module.subscribe('test/topic', callback, arg1='value1')
        self.mock_messaging_service.subscribe.assert_called_with('test/topic', callback, arg1='value1')

    def test_log(self):
        with mock.patch.object(self.module, 'publish') as mock_publish:
            self.module.log('Test message', level='debug')
            mock_publish.assert_called()
            args, kwargs = mock_publish.call_args
            self.assertTrue('log/debug' in args)
            self.assertTrue('[BaseModule.test_log' in kwargs['message'])

if __name__ == '__main__':
    unittest.main()