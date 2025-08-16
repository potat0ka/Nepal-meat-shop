#!/bin/bash
# ========================================================================
# 🍖 Nepal Meat Shop - Unix Deployment Script (Updated Jan 2025)
# One-click deployment for cleaned & optimized MongoDB platform
# ========================================================================

set -e  # Exit on any error

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📁 Working directory: $(pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}💡 $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux"
    else
        echo "Unknown"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python command (python3 or python)
get_python_cmd() {
    if command_exists python3; then
        echo "python3"
    elif command_exists python; then
        # Check if it's Python 3
        if python --version 2>&1 | grep -q "Python 3"; then
            echo "python"
        else
            return 1
        fi
    else
        return 1
    fi
}

# Function to get pip command
get_pip_cmd() {
    local python_cmd=$1
    if command_exists pip3; then
        echo "pip3"
    elif command_exists pip; then
        echo "pip"
    else
        echo "$python_cmd -m pip"
    fi
}

# Function to calculate file hash
calculate_hash() {
    if command_exists md5sum; then
        md5sum "$1" | cut -d' ' -f1
    elif command_exists md5; then
        md5 -q "$1"
    else
        # Fallback to modification time
        stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo "0"
    fi
}

# Main deployment function
main() {
    local OS=$(detect_os)
    
    print_status "========================================================================"
    print_status "🍖 Nepal Meat Shop - $OS Deployment Script"
    print_status "========================================================================"
    echo

    # Get project directory
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VENV_DIR="$PROJECT_DIR/venv"
    REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
    MAIN_FILE="$PROJECT_DIR/mongo_app.py"

    print_status "🔍 Checking Python installation..."
    
    # Check Python installation
    PYTHON_CMD=$(get_python_cmd)
    if [ $? -ne 0 ]; then
        print_error "Python 3 is not installed or not in PATH"
        if [ "$OS" = "macOS" ]; then
            print_warning "Install Python using Homebrew: brew install python3"
            print_warning "Or download from: https://www.python.org/downloads/"
        elif [ "$OS" = "Linux" ]; then
            print_warning "Install Python using your package manager:"
            print_warning "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
            print_warning "  CentOS/RHEL: sudo yum install python3 python3-pip"
            print_warning "  Fedora: sudo dnf install python3 python3-pip"
            print_warning "  Arch: sudo pacman -S python python-pip"
        fi
        exit 1
    fi

    # Get Python version and validate
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
    
    # Check Python version (must be 3.8+)
    MAJOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    MINOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
    
    if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        print_warning "Please upgrade your Python installation"
        exit 1
    fi

    # Check pip
    print_status "🔍 Checking pip installation..."
    PIP_CMD=$(get_pip_cmd "$PYTHON_CMD")
    if ! $PIP_CMD --version >/dev/null 2>&1; then
        print_error "pip is not available"
        print_warning "Please install pip for Python 3"
        exit 1
    fi
    print_success "pip is available"

    # Check if requirements.txt exists
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "requirements.txt not found in project directory"
        print_warning "Please ensure requirements.txt exists in: $PROJECT_DIR"
        exit 1
    fi

    # Create virtual environment if it doesn't exist
    FRESH_VENV=0
    if [ ! -d "$VENV_DIR" ]; then
        print_status "🔧 Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        print_success "Virtual environment created"
        FRESH_VENV=1
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_status "🔄 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    if [ $? -ne 0 ]; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    print_success "Virtual environment activated"

    # Check if we need to install/update dependencies
    INSTALL_DEPS=0
    if [ $FRESH_VENV -eq 1 ]; then
        INSTALL_DEPS=1
        print_info "Fresh virtual environment - installing dependencies..."
    else
        # Check if requirements have changed
        HASH_FILE="$VENV_DIR/requirements_hash.txt"
        if [ -f "$HASH_FILE" ]; then
            CURRENT_HASH=$(calculate_hash "$REQUIREMENTS_FILE")
            STORED_HASH=$(cat "$HASH_FILE" 2>/dev/null || echo "")
            
            if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
                INSTALL_DEPS=1
                print_info "Requirements changed - updating dependencies..."
            else
                print_success "Dependencies are up to date"
            fi
        else
            INSTALL_DEPS=1
            print_info "No dependency cache found - installing dependencies..."
        fi
    fi

    # Install/update dependencies if needed
    if [ $INSTALL_DEPS -eq 1 ]; then
        print_status "📦 Installing dependencies from requirements.txt..."
        print_info "💡 This may take a few minutes on first run..."
        
        # Upgrade pip first
        python -m pip install --upgrade pip
        if [ $? -ne 0 ]; then
            print_warning "⚠️ Warning: Failed to upgrade pip, continuing with current version"
        fi
        
        # Install requirements with better error handling
        python -m pip install -r "$REQUIREMENTS_FILE" --no-cache-dir
        if [ $? -ne 0 ]; then
            print_error "Failed to install dependencies"
            print_warning "💡 Troubleshooting tips:"
            print_warning "  1. Check your internet connection"
            print_warning "  2. Try clearing pip cache: python -m pip cache purge"
            print_warning "  3. Update pip: python -m pip install --upgrade pip"
            print_warning "  4. Install with --user flag: python -m pip install --user -r requirements.txt"
            exit 1
        fi
        
        # Store requirements hash for future checks
        calculate_hash "$REQUIREMENTS_FILE" > "$VENV_DIR/requirements_hash.txt"
        
        print_success "Dependencies installed successfully"
    fi

    # Check MongoDB connection (optional but recommended)
    print_status "🔍 Checking MongoDB availability..."
    if python -c "import pymongo; client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('MongoDB connection successful')" 2>/dev/null; then
        print_success "MongoDB is running and accessible"
    else
        print_warning "⚠️ MongoDB is not running or not accessible"
        print_warning "💡 The application will work but you may need to start MongoDB"
        if [ "$OS" = "macOS" ]; then
            print_warning "  Install with Homebrew: brew install mongodb-community"
            print_warning "  Start service: brew services start mongodb-community"
        elif [ "$OS" = "Linux" ]; then
            print_warning "  Download from: https://www.mongodb.com/try/download/community"
            print_warning "  Or install via package manager (varies by distribution)"
        fi
    fi

    # Check if main application file exists
    if [ ! -f "$MAIN_FILE" ]; then
        print_error "Main application file not found: $MAIN_FILE"
        print_warning "Available Python files in project:"
        ls -1 *.py 2>/dev/null || echo "No Python files found"
        exit 1
    fi

    # Load environment variables if .env.mongo exists
    ENV_FILE="$PROJECT_DIR/.env.mongo"
    if [ -f "$ENV_FILE" ]; then
        print_status "📄 Loading environment variables from .env.mongo..."
        set -a  # Automatically export variables
        source "$ENV_FILE"
        set +a  # Stop automatically exporting
        print_success "Environment variables loaded"
    fi

    # Set additional environment variables
    export FLASK_ENV=development
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

    # Final checks before starting
    echo
    print_status "🚀 Starting Nepal Meat Shop Application..."
    print_status "========================================================================"
    print_success "📁 Project Directory: $PROJECT_DIR"
    print_success "🐍 Python Version: $PYTHON_VERSION"
    print_success "📦 Virtual Environment: $VENV_DIR"
    print_success "🌐 Application will be available at: http://127.0.0.1:5000"
    print_status "========================================================================"
    print_warning "💡 Press Ctrl+C to stop the server"
    echo

    # Function to handle cleanup on exit
    cleanup() {
        echo
        print_status "🛑 Shutting down application..."
        print_success "Application stopped successfully"
        print_status "🛑 Deployment script finished"
    }

    # Set trap for cleanup
    trap cleanup EXIT INT TERM

    # Start the application
    python "$MAIN_FILE"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi