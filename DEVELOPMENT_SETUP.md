# EggBot Development Setup

## Environment Configuration

### Development Environment
- **Location**: Ubuntu VM
- **Purpose**: Code development, editing, and testing
- **Architecture**: x86_64
- **Tools**: Git, IDE, code analysis

### Deployment Environment
- **Location**: Raspberry Pi 4B
- **Purpose**: Production runtime environment
- **Architecture**: ARM64
- **Hardware**: GPIO pins, I2C sensors, servo control
- **Services**: pigpio daemon, temperature sensors, servo control

## Development Workflow

1. **Code Development**: Done on Ubuntu VM in `/home/jordan/Projects/EggBot/`
2. **Testing**: Code is deployed and tested on the Raspberry Pi 4B
3. **Hardware Interaction**: All GPIO, I2C, and servo operations happen on the Pi
4. **Docker Deployment**: Containers are built and run on the Raspberry Pi

## Key Considerations

- **Docker Builds**: All containers (API, UI, pigpiod) are built and run on the Pi
- **Hardware Access**: GPIO, I2C, servo control only available on Pi hardware
- **Simulation Mode**: Can be enabled for development testing on VM without hardware
- **Network Configuration**:
  - UI accessible on Pi's IP address (typically 192.168.1.194)
  - API runs on Pi using host networking or container networking
  - pigpio daemon runs in container or natively on Pi

## Files That Reference Environment

- `docker-compose.pi-native.yml` - Production deployment configuration
- `ui/nginx.conf` - API proxy configuration with Pi IP
- Environment variables in containers reference Pi-specific settings

## Common Issues and Solutions

### Docker BuildKit Hanging
If you encounter "resolving provenance for metadata file" hanging during builds:

1. **Option 1: Disable BuildKit temporarily**
   ```bash
   export DOCKER_BUILDKIT=0
   export COMPOSE_DOCKER_CLI_BUILD=0
   docker-compose -f docker-compose.pi-native.yml build
   ```

2. **Option 2: Use legacy build mode**
   ```bash
   docker-compose -f docker-compose.pi-native.yml build --no-cache --parallel
   ```

3. **Option 3: Build services individually**
   ```bash
   docker-compose -f docker-compose.pi-native.yml build api
   docker-compose -f docker-compose.pi-native.yml build pigpiod
   docker-compose -f docker-compose.pi-native.yml build ui
   ```

## Notes for Claude

- When discussing testing or deployment, assume it happens on the Raspberry Pi
- Development and code changes happen on the Ubuntu VM
- Hardware-specific issues can only be resolved on the Pi environment
- Docker container testing and debugging should be done on the Pi
- BuildKit issues are common on ARM64 platforms - provide alternatives when needed