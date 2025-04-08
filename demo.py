#!/usr/bin/env python3
"""
Mars Pathfinder Demo Script

This script demonstrates how to use the Mars Pathfinder simulator with
different configuration presets from the settings.json file.
"""

import argparse
import json
import os
import sys

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Mars Pathfinder Demo')
    
    parser.add_argument('--preset', type=str, default='test',
                        choices=['test', 'performance', 'beautiful'],
                        help='Simulation preset to use (default: test)')
    
    return parser.parse_args()

def load_settings(preset_name):
    """Load settings from the settings.json file."""
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        # Check if the requested preset exists
        if preset_name not in settings['presets']:
            print(f"Error: Preset '{preset_name}' not found in settings.json")
            return None
            
        # Start with the default settings
        preset_settings = {}
        
        # Apply the preset settings on top of defaults
        preset = settings['presets'][preset_name]
        
        # Create command line arguments based on settings
        args = ['python', 'mars_terrain_simulator.py']
        
        # Apply terrain settings
        if 'terrain' in preset:
            terrain = preset['terrain']
            if 'width' in terrain:
                args.extend(['--width', str(terrain['width'])])
            if 'height' in terrain:
                args.extend(['--height', str(terrain['height'])])
            if 'max_elevation' in terrain:
                args.extend(['--max-elevation', str(terrain['max_elevation'])])
            if 'chunk_size' in terrain:
                args.extend(['--chunk-size', str(terrain['chunk_size'])])
            if 'scale' in terrain:
                args.extend(['--scale', str(terrain['scale'])])
            if 'obstacle_prob' in terrain:
                args.extend(['--obstacle-prob', str(terrain['obstacle_prob'])])
                
        # Apply fullscreen setting
        if 'simulation' in preset and 'fullscreen' in preset['simulation'] and preset['simulation']['fullscreen']:
            args.append('--fullscreen')
            
        # Convert arguments list to command string
        command = ' '.join(args)
        return command
        
    except FileNotFoundError:
        print("Error: settings.json file not found")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in settings.json")
        return None

def main():
    """Main function to run the demo."""
    args = parse_args()
    
    # Load settings for the selected preset
    command = load_settings(args.preset)
    if not command:
        return 1
        
    # Print the command to be executed
    print(f"Running Mars Pathfinder with '{args.preset}' preset")
    print(f"Command: {command}")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nDemo cancelled")
        return 1
        
    # Execute the command
    print("\nStarting Mars Pathfinder Autopilot...")
    os.system(command)
    return 0

if __name__ == '__main__':
    sys.exit(main()) 