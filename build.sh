#!/bin/bash
# Build script for Local Brain
# Builds the React frontend and packages everything into a single executable

set -e  # Exit on error

echo "======================================"
echo "Local Brain - Build Script"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${YELLOW}PyInstaller not found. Installing...${NC}"
    pip3 install pyinstaller
fi

# Step 1: Build React frontend
echo -e "\n${BLUE}Step 1: Building React frontend...${NC}"
npm run build

if [ ! -d "dist" ]; then
    echo "Error: dist folder not found after build"
    exit 1
fi

echo -e "${GREEN}✓ React frontend built successfully${NC}"

# Step 2: Package with PyInstaller
echo -e "\n${BLUE}Step 2: Packaging with PyInstaller...${NC}"
pyinstaller local-brain.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build completed successfully!${NC}"
    echo ""
    echo "Executable location:"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  → dist/LocalBrain.app"
        echo ""
        echo "To run:"
        echo "  open dist/LocalBrain.app"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  → dist/LocalBrain"
        echo ""
        echo "To run:"
        echo "  ./dist/LocalBrain"
    else
        echo "  → dist/LocalBrain.exe"
        echo ""
        echo "To run:"
        echo "  dist\\LocalBrain.exe"
    fi
else
    echo -e "${YELLOW}Build failed. Check the output above for errors.${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "Build process complete!"
echo "======================================"
