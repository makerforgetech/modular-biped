import os
import yaml
import importlib.util
from pubsub import pub

def deep_merge(a, b):
    """Recursively merge dict b into dict a."""
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            a[k] = deep_merge(a[k], v)
        else:
            a[k] = v
    return a

class ModuleLoader:
    def __init__(self, config_folder='config', override_folder='config/overrides'):
        """
        ModuleLoader class
        :param config_folder: folder containing the module configuration files
        
        Example config file:
        config/modules.yml
        ---
        buzzer:
            enabled: true # Required
            path: "modules.audio.buzzer.Buzzer" # Required
            config: # Passed as **kwargs to the module's __init__ method
                pin: 27
                name: 'buzzer'
        
        Example:
        loader = ModuleLoader()
        modules = loader.load_modules()
        
        Reference module once loaded:
        translator_inst = modules['Translator']        
        """
        self.config_folder = config_folder
        self.override_folder = override_folder
        self.modules = self.load_yaml_files()

    def load_yaml_files(self):
        """Load and parse YAML files from the config folder, merging with local overrides if present."""
        config_files = [os.path.join(self.config_folder, f) for f in os.listdir(self.config_folder) if f.endswith('.yml')]
        loaded_modules = []
        for file_path in config_files:
            with open(file_path, 'r') as stream:
                try:
                    config = yaml.safe_load(stream)
                    # Try to load override file
                    base_filename = os.path.basename(file_path)
                    override_path = os.path.join(self.override_folder, base_filename.replace('.yml', '.local.yml'))
                    if os.path.exists(override_path):
                        with open(override_path, 'r') as o_stream:
                            override = yaml.safe_load(o_stream)
                        # Merge override into base config
                        for module_name, module_config in override.items():
                            if module_name in config:
                                config[module_name] = deep_merge(config[module_name], module_config)
                            else:
                                config[module_name] = module_config
                    for module_name, module_config in config.items():
                        if module_config.get('enabled', False):
                            loaded_modules.append(module_config)
                except yaml.YAMLError as e:
                    print(f"Error loading {file_path}: {e}")
        return loaded_modules

    def set_messaging_service(self, module_instances, messaging_service):
        """Set the messaging service for the modules."""
        # Iterate through the module instances, extract name and module
        for name, module in module_instances.items():
            # get module name from object
            # if module is not messaging_service:
            if 'MessagingService' in name:
                continue
            module.messaging_service = messaging_service

    def load_modules(self):
        """Dynamically load and instantiate the modules based on the config."""
        instances = {}  # Use a dictionary to store instances for easy access
        for module in self.modules:
            print(f"Enabling {module['path']}")
            # get path excluding the last part
            module_path = module['path'].rsplit('.', 1)[0].replace('.', '/')  # e.g., "modules.servo"
            module_name = module['path'].split('.')[-1]  # e.g., "Servo"
            instances_config = module.get('instances', [module.get('config')])  # Get all instances or just use config 
            if instances_config[0] is None:
                instances_config = [{}]

            # Dynamically load the module
            spec = importlib.util.spec_from_file_location(module_name, f"{module_path}.py")
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")

            # Create instances of the module
            for instance_config in instances_config:
                # Pass the instance config to the module's __init__ method as **kwargs
                instance_name = module_name + '_' + instance_config.get('name') if instance_config.get('name') is not None else module_name # Use the module name and instance name as the key or module_name if single instance
                instance = getattr(mod, module_name)(**instance_config)

                # Store the instance in the dictionary
                instances[instance_name] = instance
                # print(f"[ModuleLoader] Loaded module: {module_name} instance: {instance_name}")

        print("All modules loaded")
        return instances  # Return the dictionary of instances
