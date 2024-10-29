import os
import yaml
import importlib.util
from pubsub import pub

class ModuleLoader:
    def __init__(self, config_folder='config'):
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
        self.modules = self.load_yaml_files()

    def load_yaml_files(self):
        """Load and parse YAML files from the config folder."""
        config_files = [os.path.join(self.config_folder, f) for f in os.listdir(self.config_folder) if f.endswith('.yml')]
        loaded_modules = []
        for file_path in config_files:
            with open(file_path, 'r') as stream:
                try:
                    config = yaml.safe_load(stream)
                    for module_name, module_config in config.items():
                        if module_config.get('enabled', False):
                            loaded_modules.append(module_config)
                except yaml.YAMLError as e:
                    print(f"Error loading {file_path}: {e}")
        return loaded_modules

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
            spec.loader.exec_module(mod)

            # Create instances of the module
            for instance_config in instances_config:
                # Pass the instance config to the module's __init__ method as **kwargs
                instance_name = module_name + '_' + instance_config.get('name') if instance_config.get('name') is not None else module_name # Use the module name and instance name as the key or module_name if single instance
                instance = getattr(mod, module_name)(**instance_config)

                # Store the instance in the dictionary
                instances[instance_name] = instance
                pub.sendMessage('log', msg=f"[ModuleLoader] Loaded module: {module_name} instance: {instance_name}")

        print("All modules loaded")
        return instances  # Return the dictionary of instances
