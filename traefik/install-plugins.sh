#!/bin/bash
set -e

# Create plugins directory if it doesn't exist
mkdir -p /plugins

# Install required build tools
apt-get update && apt-get install -y git build-essential

# Install Go if not already installed
if ! command -v go &> /dev/null; then
    echo "Installing Go..."
    wget https://golang.org/dl/go1.21.0.linux-amd64.tar.gz
    tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
    export PATH=$PATH:/usr/local/go/bin
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    source ~/.bashrc
fi

# Set Go environment variables
export GOPATH=/go
export PATH=$PATH:$GOPATH/bin

# Create necessary directories
mkdir -p $GOPATH/src/github.com/traefik/plugins

# Install container-manager plugin
echo "Installing container-manager plugin..."
cd $GOPATH/src/github.com/traefik/plugins
git clone https://github.com/traefik/plugindemo.git
cd plugindemo
go mod download
go build -o /plugins/traefik-container-manager ./container-manager

# Install other plugins as needed
# Example:
# echo "Installing another plugin..."
# cd $GOPATH/src/github.com/traefik/plugins
# git clone https://github.com/username/plugin-repo.git
# cd plugin-repo
# go mod download
# go build -o /plugins/plugin-name ./path/to/plugin

echo "Plugins installed successfully in /plugins directory"
ls -la /plugins
