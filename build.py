#!/usr/bin/env python3
"""
Build script for Mars Terrain Simulator C++ components.

This script compiles the C++ terrain generator module for improved performance.
"""

import os
import platform
import subprocess
import sys

def build_terrain_generator():
    """Build the C++ terrain generator library."""
    print("Building C++ terrain generator...")
    
    # Change to the terrain_generator directory
    os.chdir('terrain_generator')
    
    # Check the platform to determine make command
    if platform.system() == 'Windows':
        make_cmd = ['nmake' if os.system('where nmake >nul 2>&1') == 0 else 'mingw32-make']
    else:
        make_cmd = ['make']
    
    # Run the make command
    try:
        subprocess.run(make_cmd, check=True)
        print("C++ terrain generator built successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error building C++ terrain generator: {e}", file=sys.stderr)
        print("Falling back to Python implementation (slower).", file=sys.stderr)
        return False
    
    return True

def main():
    """Main build function."""
    # Create terrain_generator directory if it doesn't exist
    if not os.path.exists('terrain_generator'):
        print("Error: terrain_generator directory not found!", file=sys.stderr)
        return 1
    
    # Build C++ terrain generator
    success = build_terrain_generator()
    
    # Return to the original directory
    os.chdir('..')
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 