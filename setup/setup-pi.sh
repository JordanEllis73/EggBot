#!/bin/bash
# setup-pi.sh - Run this script on your Raspberry Pi to prepare for deployments

set -e

echo "Setting up Raspberry Pi for automated deployments..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Create project directory
PROJECT_DIR="/home/$USER/your-project-name"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Initialize git repository (if not already done)
if [ ! -d ".git" ]; then
    git init
    git remote add origin https://github.com/your-username/your-repo-name.git
    git pull origin main
fi

# Set up SSH key for GitHub Actions (generate if needed)
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "Add this public key to your GitHub repository secrets as PI_SSH_KEY:"
    cat ~/.ssh/id_rsa.pub
fi

# Create environment file
cat > .env << EOF
# Add any environment-specific variables here
SERIAL_PORT=/dev/ttyACM0
BAUD=115200
EOF

# Set up log rotation for Docker
sudo tee /etc/logrotate.d/docker-container << EOF
/var/lib/docker/containers/*/*.log {
    rotate 5
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
EOF

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add these secrets to your GitHub repository:"
echo "   - PI_HOST: $(hostname -I | awk '{print $1}')"
echo "   - PI_USER: $USER" 
echo "   - PI_SSH_KEY: $(cat ~/.ssh/id_rsa)"
echo ""
echo "2. Update docker-compose.yml with your actual GitHub Container Registry URLs"
echo "3. Push your code to trigger the first deployment!"
echo ""
echo "Your Pi is ready for automated deployments!"
