#!/usr/bin/env python3
"""
Launch script for the Robot DeskGUI application.
This script runs on the laptop/desktop to connect to and control the robot.
"""

import os
import sys
import yaml
from DeskGUI.desk_gui import launch_gui

def load_config():
    """Load DeskGUI configuration from the YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'deskgui.yml')
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            return config_data.get('deskgui', {}).get('config', {})
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

def main():
    """Main function to launch the DeskGUI application."""
    print("Starting Robot DeskGUI...")
    
    # Load configuration
    config = load_config()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        config['robot_ip'] = sys.argv[1]
    
    # Launch the GUI application
    launch_gui(**config)

if __name__ == '__main__':
    main()
