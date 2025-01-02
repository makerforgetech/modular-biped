#!/bin/bash

# Set up Python virtual environment
python3 -m venv --system-site-packages myenv
source myenv/bin/activate

# Initialize arrays for dependencies and additional setup URLs
PYTHON_DEPENDENCIES=()
UNIX_DEPENDENCIES=()
ADDITIONAL_URLS=()
ACTIVE_MODULES=()

# Install yaml package for Python
myenv/bin/python3 -m pip install pyyaml



# Helper function to parse dependencies from YAML files using Python
parse_dependencies() {
  myenv/bin/python3 - <<EOF
import yaml, sys, os

config_file = "$1"
module_name = os.path.basename(config_file).replace('.yml', '')  # Get the module name from the filename
try:
    with open(config_file) as f:
        config = yaml.safe_load(f)
        if isinstance(config, dict):
            for section in config.values():
                # Ensure each section has 'enabled' set to true and 'dependencies' exists
                if isinstance(section, dict) and section.get('enabled', False) and 'dependencies' in section:
                    print(f"MODULE:{module_name}")
                    for dep_type, deps in section['dependencies'].items():
                        if dep_type == 'python':
                            for dep in deps:
                                print(f"PYTHON:{dep}")
                        elif dep_type == 'unix':
                            for dep in deps:
                                print(f"UNIX:{dep}")
                        elif dep_type == 'additional':
                            for url in deps:
                                print(f"ADDITIONAL:{module_name}:{url}")
except yaml.YAMLError as e:
    print(f"Error reading {config_file}: {e}", file=sys.stderr)
EOF
}

# Iterate over each YAML config file in the config directory
for config_file in config/*.yml; do
  while IFS= read -r dependency; do
    # Separate Python and Unix dependencies and capture active module names
    if [[ $dependency == MODULE:* ]]; then
      ACTIVE_MODULES+=("${dependency#MODULE:}")
    elif [[ $dependency == PYTHON:* ]]; then
      PYTHON_DEPENDENCIES+=("${dependency#PYTHON:}")
    elif [[ $dependency == UNIX:* ]]; then
      UNIX_DEPENDENCIES+=("${dependency#UNIX:}")
    elif [[ $dependency == ADDITIONAL:* ]]; then
      ADDITIONAL_URLS+=("${dependency#ADDITIONAL:}")
    fi
  done < <(parse_dependencies "$config_file")
done

# Remove duplicate dependencies
UNIQUE_PYTHON_DEPENDENCIES=($(echo "${PYTHON_DEPENDENCIES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
UNIQUE_UNIX_DEPENDENCIES=($(echo "${UNIX_DEPENDENCIES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
UNIQUE_ACTIVE_MODULES=($(echo "${ACTIVE_MODULES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
UNIQUE_ADDITIONAL_URLS=($(echo "${ADDITIONAL_URLS[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

# Update apt-get and install Unix dependencies
if [ ${#UNIQUE_UNIX_DEPENDENCIES[@]} -ne 0 ]; then
  sudo apt-get update
  for dep in "${UNIQUE_UNIX_DEPENDENCIES[@]}"; do
    sudo apt-get install -y "$dep"
  done
fi

# Install Python dependencies explicitly using the virtual environment's pip
for dep in "${UNIQUE_PYTHON_DEPENDENCIES[@]}"; do
  myenv/bin/python3 -m pip install "$dep"
done

# Set execute permissions for additional scripts
chmod 777 startup.sh stop.sh

# change permissions of installer files
chmod 777 installers/*.sh

# Summary of modules and dependencies installed
echo -e "\n==== Installation Summary ===="
echo "Active modules installed: ${#UNIQUE_ACTIVE_MODULES[@]}"
for module in "${UNIQUE_ACTIVE_MODULES[@]}"; do
  echo " - $module"
done

echo -e "\nPython dependencies installed:"
for dep in "${UNIQUE_PYTHON_DEPENDENCIES[@]}"; do
  echo " - $dep"
done

echo -e "\nUnix dependencies installed:"
for dep in "${UNIQUE_UNIX_DEPENDENCIES[@]}"; do
  echo " - $dep"
done

if [ ${#UNIQUE_ADDITIONAL_URLS[@]} -ne 0 ]; then
echo -e "\nACTION REQUIRED: Additional manual configuration required for the following modules:"
for dep in "${UNIQUE_ADDITIONAL_URLS[@]}"; do
  echo " - $dep"
done
fi
echo "============================="
