#!/bin/bash

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
    echo "Installing the $SERVICE_NAME service..."

    # Create the service file
    cat <<EOF | sudo tee "$SERVICE_FILE_PATH" > /dev/null
[Unit]
Description=Modular Biped Launcher
After=network.target

[Service]
Type=simple
ExecStart=$BASE_DIR/startup.sh
WorkingDirectory=$BASE_DIR
User=$USER
Restart=on-failure

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
        install_service
        ;;
    disable)
        remove_service
        ;;
    "")
        echo "No argument provided. Enabling the service by default."
        install_service
        echo
        echo "To disable this service, run:"
        echo "  $0 disable"
        ;;
    *)
        echo "Usage: $0 {enable|disable}"
        exit 1
        ;;
esac
