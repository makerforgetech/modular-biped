
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
# Mock pubsub before importing module_loader
import types
sys.modules['pubsub'] = types.ModuleType('pubsub')
sys.modules['pubsub'].pub = MagicMock()
# mock yaml before importing module_loader
sys.modules['yaml'] = MagicMock()
sys.modules['yaml'].safe_load = MagicMock()
import yaml
from module_loader import ModuleLoader


class TestModuleLoader(unittest.TestCase):
    """Test cases for ModuleLoader class"""

    def setUp(self):
        self.patcher_os_walk = patch('os.walk')
        self.patcher_open = patch('builtins.open', create=True)
        self.patcher_yaml = patch('yaml.safe_load')
        self.patcher_importlib_spec = patch('importlib.util.spec_from_file_location')
        self.patcher_importlib_mod = patch('importlib.util.module_from_spec')
        # Patch _load_environment_config to control enabled/override state per test
        self.patcher_env = patch.object(ModuleLoader, '_load_environment_config')
        self.mock_walk = self.patcher_os_walk.start()
        self.mock_open = self.patcher_open.start()
        self.mock_yaml = self.patcher_yaml.start()
        self.mock_spec = self.patcher_importlib_spec.start()
        self.mock_mod = self.patcher_importlib_mod.start()
        self.mock_env = self.patcher_env.start()
        # Default: no modules enabled
        self.mock_env.return_value = {}

    def tearDown(self):
        patch.stopall()

    def _setup_module_config(self, class_name='TestModule', config=None, instances=None):
        """Build a module config dict as it would appear in config.yml."""
        module_config = {
            'class': class_name,
        }
        if config is not None:
            module_config['config'] = config
        if instances is not None:
            module_config['instances'] = instances
        return {'test_module': module_config}

    def test_initialization_default_env(self):
        # Should default to 'laptop' environment
        self.mock_walk.return_value = []
        loader = ModuleLoader(config_folder='modules')
        self.assertEqual(loader.environment, 'laptop')

    def test_load_yaml_files_enabled(self):
        # Module enabled in environment config is loaded
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.return_value = self._setup_module_config()
        self.mock_env.return_value = {'test_module': {'enabled': True}}
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        self.assertEqual(len(loader.modules), 1)

    def test_load_yaml_files_disabled(self):
        # Module not in environment config (or explicitly disabled) is skipped
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.return_value = self._setup_module_config()
        self.mock_env.return_value = {'test_module': {'enabled': False}}
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        self.assertEqual(len(loader.modules), 0)

    def test_load_yaml_files_not_in_env(self):
        # Module absent from environment file is not loaded
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.return_value = self._setup_module_config()
        self.mock_env.return_value = {}  # module not listed
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        self.assertEqual(len(loader.modules), 0)

    def test_load_yaml_files_env_config_override(self):
        # Environment config values are merged over module config values
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.return_value = self._setup_module_config(config={'pin': 5, 'test_on_boot': False})
        self.mock_env.return_value = {'test_module': {'enabled': True, 'config': {'pin': 9}}}
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        self.assertEqual(len(loader.modules), 1)
        # pin should be overridden to 9, test_on_boot should still be False
        self.assertEqual(loader.modules[0]['config']['pin'], 9)
        self.assertEqual(loader.modules[0]['config']['test_on_boot'], False)

    def test_load_yaml_files_env_instances_override(self):
        # Environment instances list replaces module instances list
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        module_instances = [{'name': 'original', 'id': 0}]
        env_instances = [{'name': 'env_override', 'id': 99}]
        self.mock_yaml.return_value = self._setup_module_config(instances=module_instances)
        self.mock_env.return_value = {'test_module': {'enabled': True, 'instances': env_instances}}
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        self.assertEqual(len(loader.modules), 1)
        self.assertEqual(loader.modules[0]['instances'], env_instances)

    @patch.dict('sys.modules', {'yaml': MagicMock()})
    def test_load_yaml_files_yaml_error(self):
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.side_effect = yaml.YAMLError('YAML error')
        self.mock_env.return_value = {'test_module': {'enabled': True}}
        loader = ModuleLoader(config_folder='modules', environment='laptop')
        # Should not raise, just print error
        self.assertEqual(loader.modules, [])
        self.mock_yaml.side_effect = None

    def test_load_modules_success_and_instance_naming(self):
        # Setup for dynamic loading with two instances
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        instances = [
            {'name': 'foo', 'param': 1},
            {'name': 'bar', 'param': 2}
        ]
        self.mock_yaml.return_value = self._setup_module_config(instances=instances)
        self.mock_env.return_value = {'test_module': {'enabled': True}}
        mock_spec = MagicMock()
        self.mock_spec.return_value = mock_spec
        mock_mod = MagicMock()
        self.mock_mod.return_value = mock_mod

        class Dummy:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
        setattr(mock_mod, 'TestModule', Dummy)
        mock_spec.loader.exec_module.side_effect = lambda mod: mod.__setattr__('TestModule', Dummy)

        loader = ModuleLoader(config_folder='modules', environment='laptop')
        with patch('importlib.util.module_from_spec', return_value=mock_mod):
            instances_dict = loader.load_modules()
        self.assertIn('TestModule_foo', instances_dict)
        self.assertIn('TestModule_bar', instances_dict)
        self.assertIsInstance(instances_dict['TestModule_foo'], Dummy)
        self.assertEqual(instances_dict['TestModule_foo'].kwargs['name'], 'foo')

    def test_load_modules_no_config(self):
        # Module with no config section uses empty dict
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        module_cfg = self._setup_module_config()  # no config
        self.mock_yaml.return_value = module_cfg
        self.mock_env.return_value = {'test_module': {'enabled': True}}
        mock_spec = MagicMock()
        self.mock_spec.return_value = mock_spec
        mock_mod = MagicMock()

        class Dummy:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
        setattr(mock_mod, 'TestModule', Dummy)
        mock_spec.loader.exec_module.side_effect = lambda mod: mod.__setattr__('TestModule', Dummy)

        loader = ModuleLoader(config_folder='modules', environment='laptop')
        with patch('importlib.util.module_from_spec', return_value=mock_mod):
            instances_dict = loader.load_modules()
        self.assertIn('TestModule', instances_dict)
        self.assertIsInstance(instances_dict['TestModule'], Dummy)

    def test_load_modules_import_error(self):
        # Import error is caught and logged, does not raise
        self.mock_walk.return_value = [('modules/test', [], ['config.yml'])]
        self.mock_open.return_value.__enter__.return_value = MagicMock()
        self.mock_yaml.return_value = self._setup_module_config()
        self.mock_env.return_value = {'test_module': {'enabled': True}}
        mock_spec = MagicMock()
        self.mock_spec.return_value = mock_spec
        mock_mod = MagicMock()
        setattr(mock_mod, 'TestModule', lambda **kwargs: None)

        def raise_import(mod):
            raise Exception('Import error')
        mock_spec.loader.exec_module.side_effect = raise_import

        loader = ModuleLoader(config_folder='modules', environment='laptop')
        with patch('importlib.util.module_from_spec', return_value=mock_mod):
            instances_dict = loader.load_modules()
        self.assertIsInstance(instances_dict, dict)

    def test_set_messaging_service(self):
        class Dummy:
            def __init__(self):
                self.messaging_service = None
        modules = {
            'TestModule': Dummy(),
            'MessagingService': Dummy()
        }
        ms = object()
        ModuleLoader().set_messaging_service(modules, ms)
        self.assertIs(modules['TestModule'].messaging_service, ms)
        # MessagingService itself should not be set
        self.assertIsNot(modules['MessagingService'].messaging_service, ms)

    def test_load_environment_config_missing_file(self):
        # Missing environment file returns empty dict (with warning)
        with patch('os.path.exists', return_value=False):
            loader = ModuleLoader.__new__(ModuleLoader)
            loader.config_folder = 'modules'
            loader.environment = 'nonexistent'
            result = loader._load_environment_config()
        self.assertEqual(result, {})

    # ── inject_dependencies tests ─────────────────────────────────────────────

    def _make_loader_with_module(self, module_key='my_module', class_name='MyClass'):
        """Create a ModuleLoader with a single pre-loaded module (bypassing file I/O)."""
        loader = ModuleLoader.__new__(ModuleLoader)
        loader.config_folder = 'modules'
        loader.environment = 'laptop'
        loader.modules = [{'_module_key': module_key, '_class': class_name}]
        return loader

    def test_inject_simple_attribute(self):
        # inject: attr: TargetKey sets target.attr = instances['TargetKey']
        class Target:
            vision = None
        class Source:
            pass

        loader = self._make_loader_with_module()
        target_inst = Target()
        source_inst = Source()
        instances = {'MyClass': target_inst, 'Vision': source_inst}
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'inject': {'vision': 'Vision'}}
        }
        loader.inject_dependencies(instances)
        self.assertIs(target_inst.vision, source_inst)

    def test_inject_dict_path(self):
        # inject: attr.subkey: TargetKey sets target.attr['subkey'] = instances['TargetKey']
        class Target:
            imu = {}
        class IMU:
            pass

        loader = self._make_loader_with_module()
        target_inst = Target()
        imu_inst = IMU()
        instances = {'MyClass': target_inst, 'BNO055_imu_head': imu_inst}
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'inject': {'imu.head': 'BNO055_imu_head'}}
        }
        loader.inject_dependencies(instances)
        self.assertIs(target_inst.imu['head'], imu_inst)

    def test_inject_wildcard_pattern(self):
        # inject: servos: "Servo_*" builds a dict of {identifier: instance}
        class Target:
            servos = {}
        class ServoInst:
            def __init__(self, name):
                self.identifier = name

        loader = self._make_loader_with_module()
        target_inst = Target()
        servo_a = ServoInst('leg_l')
        servo_b = ServoInst('leg_r')
        instances = {
            'MyClass': target_inst,
            'Servo_leg_l': servo_a,
            'Servo_leg_r': servo_b,
        }
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'inject': {'servos': 'Servo_*'}}
        }
        loader.inject_dependencies(instances)
        self.assertIn('leg_l', target_inst.servos)
        self.assertIn('leg_r', target_inst.servos)
        self.assertIs(target_inst.servos['leg_l'], servo_a)
        self.assertIs(target_inst.servos['leg_r'], servo_b)

    def test_inject_missing_source_logs_and_skips(self):
        # Missing source should not raise; attribute is left unchanged
        class Target:
            vision = None

        loader = self._make_loader_with_module()
        target_inst = Target()
        instances = {'MyClass': target_inst}  # 'Vision' not present
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'inject': {'vision': 'Vision'}}
        }
        loader.inject_dependencies(instances)
        self.assertIsNone(target_inst.vision)  # unchanged

    def test_on_inject_calls_method(self):
        # on_inject: [start] calls target.start() after injection
        class Target:
            started = False
            def start(self):
                self.started = True

        loader = self._make_loader_with_module()
        target_inst = Target()
        instances = {'MyClass': target_inst}
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'on_inject': ['start']}
        }
        loader.inject_dependencies(instances)
        self.assertTrue(target_inst.started)

    def test_on_inject_string_form(self):
        # on_inject: start  (string, not list) also works
        class Target:
            called = False
            def start(self):
                self.called = True

        loader = self._make_loader_with_module()
        target_inst = Target()
        instances = {'MyClass': target_inst}
        self.mock_env.return_value = {
            'my_module': {'enabled': True, 'on_inject': 'start'}
        }
        loader.inject_dependencies(instances)
        self.assertTrue(target_inst.called)

    def test_inject_injects_messaging_service_automatically(self):
        # inject_dependencies always injects messaging service for all non-MessagingService modules
        class MessagingServiceModule:
            messaging_service = object()
        class OtherModule:
            messaging_service = None

        loader = self._make_loader_with_module()
        ms_inst = MessagingServiceModule()
        other_inst = OtherModule()
        instances = {'MessagingService': ms_inst, 'MyClass': other_inst}
        self.mock_env.return_value = {}
        loader.inject_dependencies(instances)
        self.assertIs(other_inst.messaging_service, ms_inst.messaging_service)

    def test_resolve_inject_source_simple(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        instances = {'Vision': object()}
        result = loader._resolve_inject_source('Vision', instances)
        self.assertIs(result, instances['Vision'])

    def test_resolve_inject_source_wildcard(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        class Inst:
            def __init__(self, id_):
                self.identifier = id_
        a, b = Inst('neck_pan'), Inst('neck_tilt')
        instances = {'Servo_neck_pan': a, 'Servo_neck_tilt': b, 'Other': object()}
        result = loader._resolve_inject_source('Servo_*', instances)
        self.assertEqual(set(result.keys()), {'neck_pan', 'neck_tilt'})

    def test_resolve_inject_source_wildcard_no_match(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        result = loader._resolve_inject_source('Servo_*', {'Other': object()})
        self.assertIsNone(result)

    def test_set_attr_simple(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        class TestTarget:
            vision = None
        target = TestTarget()
        loader._set_attr(target, 'vision', 'val')
        self.assertEqual(target.vision, 'val')

    def test_set_attr_dict_path(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        class TestTarget:
            imu = {}
        target = TestTarget()
        loader._set_attr(target, 'imu.head', 'val')
        self.assertEqual(target.imu['head'], 'val')

    def test_set_attr_creates_dict_if_absent(self):
        loader = ModuleLoader.__new__(ModuleLoader)
        class TestTarget:
            pass
        target = TestTarget()
        target.imu = None  # not a dict
        loader._set_attr(target, 'imu.head', 'val')
        self.assertEqual(target.imu, {'head': 'val'})


if __name__ == '__main__':
    unittest.main()
