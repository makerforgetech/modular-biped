import os
import yaml
import importlib.util
from pubsub import pub

class ModuleLoader:
    def __init__(self, config_folder='modules', environment=None, environments_folder=None):
        """
        ModuleLoader class
        :param config_folder: root folder to search for module config.yml files (searched recursively)
        :param environment: name of the environment to load (e.g. 'archie', 'laptop', 'server').
            Must match a YAML file in environments/<environment>.yml.
        :param environments_folder: folder containing per-environment YAML files.
            Defaults to 'environments' next to the project root.

        Each module lives in its own directory containing:
          - <module>.py   (Python implementation, filename matches directory name)
          - config.yml    (generic module configuration with 'class' key for the Python class name)
          - README.md     (documentation)
          - tests/        (unit tests)

        Which modules are enabled, and any device-specific configuration overrides, are
        controlled by a per-environment file:
          environments/<environment>.yml

        Example environment file (environments/archie.yml):
        ---
        messaging_service:
            enabled: true
        logwrapper:
            enabled: true
        gpio_motion:
            enabled: true
            config:            # merged over the module's generic config
                pin: 9
        bus_servo:
            enabled: true
            instances:         # replaces the module's instances list
              - name: leg_r_tilt
                id: 1
                range: [2511, 3944]

        Example module config.yml (modules/gpio/motion/config.yml):
        ---
        gpio_motion:
            class: Motion      # Python class name (required)
            config:            # generic defaults (device-specific values go in environment file)
                test_on_boot: false

        Example:
        loader = ModuleLoader(environment='laptop')
        modules = loader.load_modules()

        Reference module once loaded:
        translator_inst = modules['Translator']
        """
        self.config_folder = config_folder
        self.environment = environment or 'laptop'
        # Resolve environments folder: use provided value, or 'environments' at the project root
        # module_loader.py lives in src/, so project root is one level up
        _src_dir = os.path.dirname(os.path.abspath(__file__))
        _project_root = os.path.dirname(_src_dir)
        self.environments_folder = environments_folder or os.path.join(_project_root, 'environments')
        print(f"[ModuleLoader] Loading modules for environment: {self.environment}")
        self.modules = self.load_yaml_files()

    def _load_environment_config(self):
        """Load the environment YAML file to determine which modules are active and their overrides."""
        env_file = os.path.join(self.environments_folder, f'{self.environment}.yml')
        if not os.path.exists(env_file):
            print(f"[ModuleLoader] Warning: environment file not found: {env_file}")
            return {}
        with open(env_file, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"Error loading {env_file}: {e}")
                return {}

    def load_yaml_files(self):
        """Recursively search config_folder for config.yml files and load enabled module configurations."""
        env_config = self._load_environment_config()

        config_files = []
        for root, dirs, files in os.walk(self.config_folder):
            for f in files:
                if f == 'config.yml':
                    config_files.append(os.path.join(root, f))

        loaded_modules = []
        for file_path in config_files:
            with open(file_path, 'r') as stream:
                try:
                    config = yaml.safe_load(stream)
                    for module_name, module_config in config.items():
                        # Check if this module is enabled in the environment file
                        env_entry = env_config.get(module_name, {})
                        if not env_entry.get('enabled', False):
                            continue
                        print(f"[ModuleLoader] Loading module: {module_name}")

                        # Merge environment config overrides into module config (shallow merge)
                        env_config_override = env_entry.get('config', {})
                        if env_config_override:
                            module_config['config'] = {**(module_config.get('config') or {}), **env_config_override}

                        # Environment can also supply/override the instances list
                        if 'instances' in env_entry:
                            module_config['instances'] = env_entry['instances']

                        # Infer the Python file path from the config.yml directory
                        dir_path = os.path.dirname(file_path)
                        dir_name = os.path.basename(dir_path)
                        module_config['_py_file'] = os.path.join(dir_path, f"{dir_name}.py")
                        module_config['_class'] = module_config.get('class')
                        module_config['_module_key'] = module_name
                        loaded_modules.append(module_config)
                except yaml.YAMLError as e:
                    print(f"Error loading {file_path}: {e}")
        return loaded_modules

    def set_messaging_service(self, module_instances, messaging_service):
        """Set the messaging service for the modules."""
        for name, module in module_instances.items():
            if 'MessagingService' in name:
                continue
            module.messaging_service = messaging_service

    def inject_dependencies(self, instances):
        """
        Inject module dependencies as declared in the environment YAML file and wire
        the messaging service.  Call this once after load_modules().

        Each module in the environment file can declare:

            inject:
                attr_name: TargetInstanceKey         # simple attribute injection
                attr_name: "Prefix_*"                # wildcard → {inst.identifier: inst} dict
                dict_attr.subkey: TargetInstanceKey  # dict-path (e.g. imu.head, imu.body)

            on_inject:
                - method_name                        # method(s) to call after all injections

        The messaging service is always injected first for all loaded modules.

        Example (modules/environments/archie.yml):
        ---
        personality:
          inject:
            servos: "Servo_*"
            imu.head: BNO055_imu_head
            imu.body: BNO055_imu_body
            vision: Vision
        controller_handler:
          inject:
            controller: XboxController
          on_inject:
            - start
        """
        # Step 1: inject messaging service for all modules
        if 'MessagingService' in instances:
            messaging_service = instances['MessagingService'].messaging_service
            self.set_messaging_service(instances, messaging_service)

        # Step 2: build a map from environment module_key → instance keys
        module_key_to_instances = {}
        for module in self.modules:
            module_key = module.get('_module_key')
            class_name = module.get('_class')
            if not module_key or not class_name:
                continue
            related = [k for k in instances if k == class_name or k.startswith(class_name + '_')]
            module_key_to_instances[module_key] = related

        # Step 3: process inject / on_inject declarations from the environment config
        env_config = self._load_environment_config()
        for module_key, env_entry in env_config.items():
            inject_map = env_entry.get('inject', {})
            on_inject = env_entry.get('on_inject', [])
            if not inject_map and not on_inject:
                continue

            target_keys = module_key_to_instances.get(module_key, [])
            for target_key in target_keys:
                target = instances.get(target_key)
                if target is None:
                    continue

                for attr_path, source_spec in inject_map.items():
                    value = self._resolve_inject_source(source_spec, instances)
                    if value is None:
                        print(f"[ModuleLoader] inject: source '{source_spec}' not found for {target_key}.{attr_path}")
                        continue
                    self._set_attr(target, attr_path, value)
                    print(f"[ModuleLoader] inject: {target_key}.{attr_path} = {source_spec}")

                if isinstance(on_inject, str):
                    on_inject = [on_inject]
                for method_name in on_inject:
                    method = getattr(target, method_name, None)
                    if callable(method):
                        print(f"[ModuleLoader] on_inject: {target_key}.{method_name}()")
                        method()
                    else:
                        print(f"[ModuleLoader] on_inject: {target_key}.{method_name} not found or not callable")

    def _resolve_inject_source(self, source_spec, instances):
        """
        Resolve an inject source specification to a value.

        - "InstanceKey"   → instances['InstanceKey']
        - "Prefix_*"      → {inst.identifier (or key_suffix): inst} for all matching keys
        """
        if '*' in str(source_spec):
            prefix = source_spec.replace('*', '')
            result = {}
            for key, inst in instances.items():
                if key.startswith(prefix):
                    id_key = getattr(inst, 'identifier', None) or key[len(prefix):]
                    result[id_key] = inst
            return result if result else None
        return instances.get(source_spec)

    def _set_attr(self, target, attr_path, value):
        """
        Set an attribute on target using dotted path notation.

        - "vision"    → target.vision = value
        - "imu.head"  → target.imu['head'] = value  (creates dict if absent)
        """
        if '.' in attr_path:
            attr_name, sub_key = attr_path.split('.', 1)
            container = getattr(target, attr_name, None)
            if isinstance(container, dict):
                container[sub_key] = value
            else:
                setattr(target, attr_name, {sub_key: value})
        else:
            setattr(target, attr_path, value)

    def load_modules(self):
        """Dynamically load and instantiate the modules based on the config."""
        instances = {}  # Use a dictionary to store instances for easy access
        for module in self.modules:
            py_file = module['_py_file']
            class_name = module['_class']
            print(f"Enabling {class_name} from {py_file}")
            instances_config = module.get('instances', [module.get('config')])
            shared_config = module.get('config', {})
            if instances_config[0] is None:
                instances_config = [{}]

            # Dynamically load the module from its inferred file path
            spec = importlib.util.spec_from_file_location(class_name, py_file)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Error loading module {class_name}: {e}")

            # If multiple instances, merge shared config into each instance config
            multiple_instances = 'instances' in module and isinstance(module['instances'], list) and len(module['instances']) > 0
            for instance_config in instances_config:
                if multiple_instances:
                    # Avoid overwriting instance-specific keys with shared config
                    merged_config = {**shared_config, **instance_config}
                else:
                    merged_config = instance_config
                instance_name = class_name + '_' + instance_config.get('name') if instance_config.get('name') is not None else class_name
                instance = getattr(mod, class_name)(**merged_config)
                instances[instance_name] = instance

        print("All modules loaded")
        return instances
