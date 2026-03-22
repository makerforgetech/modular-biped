import os, sys
import signal

# Ensure src/ is on the path so module imports work when running from project root
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from modules.config import Config
from module_loader import ModuleLoader

def main():
    print('Starting...')
    # Throw exception to safely exit script when terminated
    signal.signal(signal.SIGTERM, Config.exit)

    # Get environment argument (default to 'laptop') using argparse
    import argparse
    parser = argparse.ArgumentParser(description="Makerforge Modular Robot")
    parser.add_argument('--env', default='laptop', help="Set the environment (e.g. archie, buddy, cody, server, laptop)")
    args = parser.parse_args()
    env = args.env

    # Dynamically load and initialize modules, passing env
    # config_folder is relative to src/ (the directory containing this file)
    modules_folder = os.path.join(_SRC_DIR, "modules")
    loader = ModuleLoader(config_folder=modules_folder, environment=env)
    module_instances = loader.load_modules()

    # Inject messaging service and all module-to-module dependencies declared in the
    # environment YAML file (inject: / on_inject: blocks).
    loader.inject_dependencies(module_instances)

    # Use the new SystemLoop class to run the main loop
    from system_loop import SystemLoop
    system_loop = SystemLoop(module_instances['MessagingService'].messaging_service, module_instances)
    system_loop.start()

if __name__ == '__main__':
    main()
