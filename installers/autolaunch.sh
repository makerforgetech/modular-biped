#!/bin/bash

# Usage:
#   ./autolaunch.sh [enable [<environment>] | disable]
#
# <environment> is the device configuration to use (e.g. archie, buddy, cody, server, laptop).
# Defaults to 'laptop' when not specified.
# Available environments: environments/*.yml

# Get the current user
USER=$(whoami)

# Dynamically determine the base directory (parent of the installers folder)
SCRIPT_DIR=$(dirname "$(realpath "$0")")
BASE_DIR=$(dirname "$SCRIPT_DIR")
LAST_DIR=$(basename "$BASE_DIR")

SERVICE_NAME="$LAST_DIR-launcher.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_NAME"

# Function to install the service
install_service() {
    local ENV_NAME="${1:-laptop}"
    echo "Installing the $SERVICE_NAME service for environment: $ENV_NAME..."

    # Validate that the environment file exists
    ENV_FILE="$BASE_DIR/environments/$ENV_NAME.yml"
    if [ ! -f "$ENV_FILE" ]; then
        echo "Error: Environment file not found: $ENV_FILE"
        echo "Available environments:"
        ls "$BASE_DIR/environments/" 2>/dev/null | sed 's/\.yml//' | sed 's/^/  /'
        exit 1
    fi

    # Create the service file
    cat <<EOF | sudo tee "$SERVICE_FILE_PATH" > /dev/null
[Unit]
Description=Modular Robot Launcher ($ENV_NAME)
After=network.target

[Service]
Type=simple
ExecStart=$BASE_DIR/startup.sh $ENV_NAME
WorkingDirectory=$BASE_DIR
User=$USER
Restart=on-failure
EnvironmentFile=/home/$USER/.myenv

[Install]
WantedBy=multi-user.target
EOF

    echo "Service file created at $SERVICE_FILE_PATH"

    # Reload systemd to pick up the new service
    sudo systemctl daemon-reload

    # Enable and start the service
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME

    echo "$SERVICE_NAME has been installed and started."

    echo "To debug issues, run:"
    echo "sudo journalctl -u $SERVICE_NAME -f"

    echo "IMPORTANT: Ensure that environment variables are set in /home/$USER/.myenv for the service to function properly: E.g:"
    echo "OPENAI_API_KEY=<yourkey>"
    echo "etc for: TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, ELEVENLABS_KEY as required"
}

# Function to remove the service
remove_service() {
    echo "Removing the $SERVICE_NAME service..."

    # Stop and disable the service
    sudo systemctl stop $SERVICE_NAME
    sudo systemctl disable $SERVICE_NAME

    # Remove the service file
    sudo rm -f "$SERVICE_FILE_PATH"

    # Reload systemd to apply changes
    sudo systemctl daemon-reload

    echo "$SERVICE_NAME has been removed."
}

# Parse user input
case "$1" in
    enable)
        install_service "$2"
        ;;
    disable)
        remove_service
        ;;
    "")
        echo "No argument provided. Enabling the service with default environment (laptop)."
        install_service "laptop"
        echo
        echo "To use a different environment, run:"
        echo "  $0 enable <environment>   (e.g. $0 enable buddy)"
        echo
        echo "To disable this service, run:"
        echo "  $0 disable"
        ;;
    *)
        echo "Usage: $0 [enable [<environment>] | disable]"
        echo "Available environments:"
        ls "$BASE_DIR/environments/" 2>/dev/null | sed 's/\.yml//' | sed 's/^/  /'
        exit 1
        ;;
esac
