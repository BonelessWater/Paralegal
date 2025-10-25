#!/bin/bash
# Pre-Model Setup Script for AI Legal Tender Hackathon
# Run this BEFORE your teammate selects the model
# This prepares the AMD infrastructure without downloading any models

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║    AI Legal Tender - Pre-Model Infrastructure Setup             ║"
echo "║    AMD MI300X + vLLM + Docker Preparation                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track progress
STEP=1
TOTAL_STEPS=7

print_step() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}[$STEP/$TOTAL_STEPS]${NC} $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ((STEP++))
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# ============================================================================
# STEP 1: Verify ROCm and GPU
# ============================================================================
print_step "Verifying AMD GPU and ROCm Installation"

if command -v rocm-smi &> /dev/null; then
    success "ROCm tools found (rocm-smi)"
    
    echo ""
    echo "GPU Status:"
    rocm-smi
    
    echo ""
    echo "GPU Details:"
    rocminfo | grep -E "Name|Memory" | head -10
    
    success "ROCm verification complete"
    
    echo ""
    echo -e "${YELLOW}💡 TIP: Screenshot the above GPU info for your demo deck!${NC}"
else
    error "ROCm not found!"
    echo ""
    echo "ROCm is required for AMD GPU acceleration."
    echo "Install from: https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html"
    echo ""
    read -p "Continue anyway? (not recommended) [y/N]: " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        exit 1
    fi
fi

# ============================================================================
# STEP 2: Check/Install Docker
# ============================================================================
print_step "Checking Docker Installation"

if command -v docker &> /dev/null; then
    success "Docker is already installed"
    docker --version
    
    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        success "Docker daemon is running"
    else
        warning "Docker installed but daemon not running"
        echo "Attempting to start Docker..."
        sudo systemctl start docker
        
        if docker ps &> /dev/null; then
            success "Docker daemon started successfully"
        else
            error "Could not start Docker daemon"
            echo "Try: sudo systemctl start docker"
            exit 1
        fi
    fi
    
    # Check if user is in docker group
    if groups | grep -q docker; then
        success "User is in docker group"
    else
        warning "User not in docker group - may need sudo for docker commands"
        read -p "Add current user to docker group? [Y/n]: " ADD_GROUP
        if [ "$ADD_GROUP" != "n" ] && [ "$ADD_GROUP" != "N" ]; then
            sudo usermod -aG docker $USER
            success "Added to docker group - log out and back in for changes to take effect"
        fi
    fi
else
    warning "Docker not found - installing..."
    
    # Download and install Docker
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    
    if [ $? -eq 0 ]; then
        success "Docker installed successfully"
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        # Start docker
        sudo systemctl start docker
        sudo systemctl enable docker
        
        success "Docker configured and started"
        warning "You may need to log out and back in for docker group permissions"
    else
        error "Docker installation failed"
        exit 1
    fi
fi

# ============================================================================
# STEP 3: Verify Docker GPU Access
# ============================================================================
print_step "Verifying Docker GPU Access"

if [ -e /dev/kfd ] && [ -e /dev/dri ]; then
    success "GPU device files exist (/dev/kfd, /dev/dri)"
    ls -la /dev/kfd /dev/dri 2>/dev/null | head -5
else
    error "Missing GPU device files - Docker won't be able to access GPU"
    echo "This may indicate ROCm is not properly installed"
    exit 1
fi

# Check render group permissions
if groups | grep -q render; then
    success "User is in render group (GPU access)"
else
    warning "User not in render group"
    read -p "Add current user to render group for GPU access? [Y/n]: " ADD_RENDER
    if [ "$ADD_RENDER" != "n" ] && [ "$ADD_RENDER" != "N" ]; then
        sudo usermod -aG render $USER
        success "Added to render group - log out and back in for changes to take effect"
    fi
fi

# ============================================================================
# STEP 4: Pull vLLM Docker Image
# ============================================================================
print_step "Pulling AMD vLLM Docker Image"

echo "This image is pre-configured with ROCm - saves 2-3 hours of manual setup!"
echo "Size: ~10-15GB (this may take 5-15 minutes depending on connection)"
echo ""

read -p "Pull vLLM Docker image now? [Y/n]: " PULL_IMAGE
if [ "$PULL_IMAGE" != "n" ] && [ "$PULL_IMAGE" != "N" ]; then
    docker pull rocm/vllm:latest
    
    if [ $? -eq 0 ]; then
        success "vLLM Docker image downloaded successfully"
        
        # Show image info
        echo ""
        echo "Image details:"
        docker images rocm/vllm:latest
    else
        error "Failed to pull vLLM image"
        echo "Check your internet connection and Docker setup"
        exit 1
    fi
else
    warning "Skipped vLLM image download - you'll need to pull it later"
fi

# ============================================================================
# STEP 5: Create Project Directory Structure
# ============================================================================
print_step "Creating Project Directory Structure"

PROJECT_DIR="$HOME/ai-legal-tender"

if [ -d "$PROJECT_DIR" ]; then
    warning "Directory $PROJECT_DIR already exists"
    read -p "Use existing directory? [Y/n]: " USE_EXISTING
    if [ "$USE_EXISTING" == "n" ] || [ "$USE_EXISTING" == "N" ]; then
        echo "Please remove or rename the existing directory first"
        exit 1
    fi
else
    mkdir -p "$PROJECT_DIR"/{models,data,logs,scripts}
    success "Created directory structure at $PROJECT_DIR"
fi

# Verify structure
if [ -d "$PROJECT_DIR/models" ] && [ -d "$PROJECT_DIR/data" ] && \
   [ -d "$PROJECT_DIR/logs" ] && [ -d "$PROJECT_DIR/scripts" ]; then
    success "All subdirectories verified"
    
    echo ""
    echo "Directory structure:"
    tree -L 2 "$PROJECT_DIR" 2>/dev/null || ls -la "$PROJECT_DIR"
else
    # Create missing directories
    mkdir -p "$PROJECT_DIR"/{models,data,logs,scripts}
    success "Directory structure created/repaired"
fi

# ============================================================================
# STEP 6: Setup Environment Variables (Optional)
# ============================================================================
print_step "Setting Up Environment Variables"

echo "Setting up environment for vLLM and Hugging Face..."

# Add to bashrc if not already present
if ! grep -q "ai-legal-tender" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# AI Legal Tender Hackathon - Environment Setup
export AI_LEGAL_TENDER_HOME="$HOME/ai-legal-tender"
export PATH="$AI_LEGAL_TENDER_HOME/scripts:$PATH"
EOF
    success "Added environment variables to ~/.bashrc"
else
    success "Environment variables already configured"
fi

# Setup Hugging Face token (if they have it now)
echo ""
echo "Hugging Face Token Setup (optional - can do this later)"
echo "Get your token from: https://huggingface.co/settings/tokens"
echo ""
read -p "Do you have your Hugging Face token now? [y/N]: " HAS_TOKEN

if [ "$HAS_TOKEN" == "y" ] || [ "$HAS_TOKEN" == "Y" ]; then
    read -p "Enter your Hugging Face token: " HF_TOKEN
    
    if [ ! -z "$HF_TOKEN" ]; then
        # Add to bashrc
        if ! grep -q "HUGGING_FACE_HUB_TOKEN" ~/.bashrc; then
            echo "export HUGGING_FACE_HUB_TOKEN=\"$HF_TOKEN\"" >> ~/.bashrc
            success "Hugging Face token saved to ~/.bashrc"
        else
            # Update existing token
            sed -i "s/export HUGGING_FACE_HUB_TOKEN=.*/export HUGGING_FACE_HUB_TOKEN=\"$HF_TOKEN\"/" ~/.bashrc
            success "Hugging Face token updated in ~/.bashrc"
        fi
        
        # Set for current session
        export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
        success "Token set for current session"
    fi
else
    warning "Skipped Hugging Face token - your teammate can set this later"
    echo "They'll need it to download models. To set it later:"
    echo "  echo 'export HUGGING_FACE_HUB_TOKEN=your_token_here' >> ~/.bashrc"
fi

# ============================================================================
# STEP 7: Verify Network Connectivity
# ============================================================================
print_step "Verifying Network Connectivity"

echo "Checking connection to Hugging Face..."
if ping -c 1 huggingface.co &> /dev/null; then
    success "Can reach Hugging Face Hub"
else
    warning "Cannot reach huggingface.co - check network connection"
    echo "You'll need this for downloading models later"
fi

echo ""
echo "Checking connection to Docker Hub..."
if ping -c 1 hub.docker.com &> /dev/null; then
    success "Can reach Docker Hub"
else
    warning "Cannot reach Docker Hub"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ SETUP COMPLETE!                             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

success "ROCm and GPU verified"
success "Docker installed and configured"
success "vLLM Docker image downloaded"
success "Project directory structure created"
success "Environment variables configured"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEXT STEPS - For Your Teammate:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Choose their legal Hugging Face model"
echo "   → Configure in .env file"
echo ""
echo "2. Download the model:"
echo "   → cd setup && ./download_model_enhanced.sh"
echo ""
echo "3. Start vLLM server:"
echo "   → ./start_vllm.sh"
echo ""
echo "4. Test everything:"
echo "   → ./test_model.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WHAT YOU CAN DO NOW:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• Work on Google ADK orchestrator setup"
echo "• Build approval interface UI"
echo "• Set up email/SMS/voice outreach automation"
echo "• Create mock legal data for testing"
echo "• Prepare demo presentation"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save setup info for reference
cat > "$PROJECT_DIR/SETUP_INFO.txt" << EOF
AI Legal Tender - Setup Information
Generated: $(date)

ROCm Version: $(rocm-smi --version 2>/dev/null | head -n 1 || echo "Unknown")
Docker Version: $(docker --version 2>/dev/null || echo "Unknown")
vLLM Image: $(docker images rocm/vllm:latest --format "{{.Repository}}:{{.Tag}} ({{.Size}})" 2>/dev/null || echo "Not pulled")

Project Directory: $PROJECT_DIR
Hugging Face Token Set: $([ ! -z "$HUGGING_FACE_HUB_TOKEN" ] && echo "Yes" || echo "No")

Setup completed successfully!
Ready for model download and vLLM deployment.
EOF

success "Setup information saved to $PROJECT_DIR/SETUP_INFO.txt"

echo ""
echo -e "${GREEN}Infrastructure is ready! 🚀${NC}"
echo ""

# Remind about logout if needed
if groups | grep -q docker && groups | grep -q render; then
    success "All permissions configured"
else
    echo ""
    warning "IMPORTANT: Log out and back in for group permissions to take effect!"
    echo "Or run: newgrp docker && newgrp render"
fi

echo ""
