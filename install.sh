#!/bin/bash

# Set up Python virtual environment
python3 -m venv --system-site-packages myenv
source myenv/bin/activate

# Initialize arrays for dependencies and active module names
PYTHON_DEPENDENCIES=()
UNIX_DEPENDENCIES=()
ACTIVE_MODULES=()

# Helper function to parse dependencies from YAML files using Python
parse_dependencies() {
  myenv/bin/python3 - <<EOF
import yaml, sys, os

config_file = "$1"
module_name = os.path.basename(config_file).replace('.yml', '')  # Get the module name from the filename
try:
    with open(config_file) as f:
        config = yaml.safe_load(f)
        # Check if the top level of the config is a dictionary to avoid AttributeError
        if isinstance(config, dict):
            for section in config.values():
                # Check if module is active before parsing dependencies
                if isinstance(section, dict) and section.get('enabled') is True:
                    print(f"MODULE:{module_name}")
                    if 'dependencies' in section:
                        for dep_type, deps in section['dependencies'].items():
                            if dep_type == 'python':
                                for dep in deps:
                                    print(f"PYTHON:{dep}")
                            elif dep_type == 'unix':
                                for dep in deps:
                                    print(f"UNIX:{dep}")
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
    fi
  done < <(parse_dependencies "$config_file")
done

# Remove duplicate dependencies
UNIQUE_PYTHON_DEPENDENCIES=($(echo "${PYTHON_DEPENDENCIES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
UNIQUE_UNIX_DEPENDENCIES=($(echo "${UNIX_DEPENDENCIES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
UNIQUE_ACTIVE_MODULES=($(echo "${ACTIVE_MODULES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

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
echo "============================="
