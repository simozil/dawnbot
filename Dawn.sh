#!/bin/bash

# Path to save the script
SCRIPT_PATH="$HOME/Dawn.sh"

# Check if the script is running as root user
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root."
    echo "Try using the 'sudo -i' command to switch to the root user, then run this script again."
    exit 1
fi

# Check and install Node.js and npm
function install_nodejs_and_npm() {
    if command -v node > /dev/null 2>&1; then
        echo "Node.js is already installed"
    else
        echo "Node.js is not installed, installing..."
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    if command -v npm > /dev/null 2>&1; then
        echo "npm is already installed"
    else
        echo "npm is not installed, installing..."
        sudo apt-get install -y npm
    fi
}

# Check and install PM2
function install_pm2() {
    if command -v pm2 > /dev/null 2>&1; then
        echo "PM2 is already installed"
    else
        echo "PM2 is not installed, installing..."
        npm install pm2@latest -g
    fi
}

# Install Python package manager pip3
function install_pip() {
    if ! command -v pip3 > /dev/null 2>&1; then
        echo "pip3 is not installed, installing..."
        sudo apt-get install -y python3-pip
    else
        echo "pip3 is already installed"
    fi
}

# Install Python packages
function install_python_packages() {
    echo "Installing Python packages..."
    pip3 install pillow ddddocr requests loguru
}

# Function to install and start Dawn
function install_and_start_dawn() {
    # Update and install necessary software
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl iptables build-essential git wget jq make gcc nano tmux htop nvme-cli pkg-config libssl-dev libleveldb-dev tar clang bsdmainutils ncdu unzip lz4 snapd

    # Install Node.js, npm, PM2, pip3, and Python packages
    install_nodejs_and_npm
    install_pm2
    install_pip
    install_python_packages

    # Get username and password
    read -r -p "Enter email: " DAWNUSERNAME
    export DAWNUSERNAME=$DAWNUSERNAME
    read -r -p "Enter password: " DAWNPASSWORD
    export DAWNPASSWORD=$DAWNPASSWORD

    echo "$DAWNUSERNAME:$DAWNPASSWORD" > password.txt

    wget -O dawn.py https://raw.githubusercontent.com/sdohuajia/Dawn/main/dawn.py

    # Start Dawn
    pm2 start python3 --name dawn -- dawn.py
}

# Function to view logs
function view_logs() {
    echo "Viewing Dawn logs..."
    pm2 log dawn
    # Wait for the user to press any key to return to the main menu
    read -p "Press any key to return to the main menu..."
}

# Function to stop and remove Dawn
function stop_and_remove_dawn() {
    if pm2 list | grep -q "dawn"; then
        echo "Stopping Dawn..."
        pm2 stop dawn
        echo "Removing Dawn..."
        pm2 delete dawn
    else
        echo "Dawn is not running"
    fi

    # Wait for the user to press any key to return to the main menu
    read -p "Press any key to return to the main menu..."
}

# Main menu function
function main_menu() {
    while true; do
        clear
        echo "Script created by the DaDu community, Twitter @ferdie_jhovie, open-source and free, do not believe anyone asking for a fee"
        echo "================================================================"
        echo "Node community Telegram group: https://t.me/niuwuriji"
        echo "Node community Telegram channel: https://t.me/niuwuriji"
        echo "Node community Discord: https://discord.gg/GbMV5EcNWF"
        echo "To exit the script, press ctrl + C"
        echo "Select an action to perform:"
        echo "1) Install and start Dawn"
        echo "2) View logs"
        echo "3) Stop and remove Dawn"
        echo "4) Exit"

        read -p "Enter your choice [1-4]: " choice

        case $choice in
            1)
                install_and_start_dawn
                ;;
            2)
                view_logs
                ;;
            3)
                stop_and_remove_dawn
                ;;
            4)
                echo "Exiting script..."
                exit 0
                ;;
            *)
                echo "Invalid option, please try again."
                read -n 1 -s -r -p "Press any key to continue..."
                ;;
        esac
    done
}

# Run the main menu
main_menu
