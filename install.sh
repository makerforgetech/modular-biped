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




# Helper function to parse dependencies from YAML files using Python, respecting environment
parse_dependencies() {
  myenv/bin/python3 - <<EOF
import yaml, sys, os

config_file = "$1"
env = "$2" or 'robot'
module_name = os.path.basename(os.path.dirname(config_file))
try:
  with open(config_file) as f:
    config = yaml.safe_load(f)
    # Expect structure: {module_name: {config: ..., dependencies: ...}}
    section = config.get(module_name)
    if section:
      # Check if enabled (if present in config)
      enabled = section.get('enabled', True)
      if not enabled:
        sys.exit(0)
      # Environment filtering logic
      env_field = section.get('environment')
      if env_field is not None:
        if isinstance(env_field, str):
          if env_field != env:
            sys.exit(0)
        elif isinstance(env_field, list):
          if env not in env_field:
            sys.exit(0)
      # Print dependencies
      if 'dependencies' in section:
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


# Determine environment YAML (default to environments/server.yml)
if [ -z "$1" ]; then
  ENV_YAML="environments/server.yml"
else
  ENV_YAML="environments/$1.yml"
fi

# Helper: get enabled modules from environment YAML
get_enabled_modules() {
  myenv/bin/python3 - <<EOF
import yaml, sys
with open("$ENV_YAML") as f:
    env = yaml.safe_load(f)
    for mod, conf in env.items():
        if isinstance(conf, dict) and conf.get('enabled', False):
            print(mod)
EOF
}

# Find config.yml for each enabled module and parse dependencies
for mod in $(get_enabled_modules); do
  # Find config.yml in any subdirectory named after the module, at any depth
  config_path=$(find src/modules -type d -name "$mod" | while read moddir; do
    if [ -f "$moddir/config.yml" ]; then
      echo "$moddir/config.yml"
    fi
  done | head -n1)
  if [ -n "$config_path" ]; then
    while IFS= read -r dependency; do
      if [[ $dependency == MODULE:* ]]; then
        ACTIVE_MODULES+=("${dependency#MODULE:}")
      elif [[ $dependency == PYTHON:* ]]; then
        PYTHON_DEPENDENCIES+=("${dependency#PYTHON:}")
      elif [[ $dependency == UNIX:* ]]; then
        UNIX_DEPENDENCIES+=("${dependency#UNIX:}")
      elif [[ $dependency == ADDITIONAL:* ]]; then
        ADDITIONAL_URLS+=("${dependency#ADDITIONAL:}")
      fi
    done < <(parse_dependencies "$config_path" "$ENVIRONMENT")
  fi
done

# Optionally, print main Python files for each active module
echo -e "\nActive module main files:"
for mod in $(get_enabled_modules); do
  pyfile=$(find src/modules -type f -name "*.py" | grep "/$mod/" | head -n1)
  if [ -n "$pyfile" ]; then
    echo " - $mod: $pyfile"
  fi
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

# Tell the user about autolaunch
echo -e "\nTo enable autolaunch on boot, run the following command:"
echo "installers/autolaunch.sh enable"
echo "To disable autolaunch, run:"
echo "installers/autolaunch.sh disable"

echo "============================="
