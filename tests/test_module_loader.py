import unittest
from unittest import mock
from module_loader import ModuleLoader

class TestModuleLoader(unittest.TestCase):

    @mock.patch('os.listdir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data="""
    buzzer:
        enabled: true
        path: "modules.audio.buzzer.Buzzer"
        config:
            pin: 27
            name: 'buzzer'
    """)
    def test_load_yaml_files(self, mock_open, mock_listdir):
        # Mock the listdir to return a list of YAML files
        mock_listdir.return_value = ['modules.yml']

        loader = ModuleLoader(config_folder='config')
        modules = loader.load_yaml_files()

        # Check if the modules list is correctly populated
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0]['path'], "modules.audio.buzzer.Buzzer")
        self.assertTrue(modules[0]['enabled'])

    @mock.patch('os.listdir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data="""
    buzzer:
        enabled: false
        path: "modules.audio.buzzer.Buzzer"
        config:
            pin: 27
            name: 'buzzer'
    """)
    def test_load_yaml_files_disabled_module(self, mock_open, mock_listdir):
        # Mock the listdir to return a list of YAML files
        mock_listdir.return_value = ['modules.yml']

        loader = ModuleLoader(config_folder='config')
        modules = loader.load_yaml_files()

        # Check if the modules list is empty since the module is disabled
        self.assertEqual(len(modules), 0)

if __name__ == '__main__':
    unittest.main()