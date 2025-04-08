#!/usr/bin/env python3
"""
Mars Terrain Simulator

A full-screen GUI simulation of Mars terrain with pathfinding and navigation.
"""

import argparse
import sys
import os
import time

from mars_terrain.terrain import TerrainGenerator, PathFinder
from mars_terrain.gui import GUI, Camera, Minimap, TerrainRenderer
from mars_terrain.control import PlayerController, InputHandler

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Mars Terrain Simulator')
    
    parser.add_argument('--width', type=int, default=15000,
                        help='Width of the terrain in blocks (default: 15000)')
    parser.add_argument('--height', type=int, default=15000,
                        help='Height of the terrain in blocks (default: 15000)')
    parser.add_argument('--max-elevation', type=int, default=250,
                        help='Maximum elevation in blocks (default: 250)')
    parser.add_argument('--chunk-size', type=int, default=256,
                        help='Size of terrain chunks (default: 256)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for terrain generation (default: random)')
    parser.add_argument('--fullscreen', action='store_true',
                        help='Run in fullscreen mode')
    parser.add_argument('--scale', type=float, default=0.01,
                        help='Terrain scale factor (default: 0.01)')
    parser.add_argument('--obstacle-prob', type=float, default=0.05,
                        help='Probability of obstacles (default: 0.05)')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode with smaller world size')
    
    return parser.parse_args()

def ensure_valid_starting_position(terrain, start_pos, radius=5):
    """
    Ensure that the starting position and its surroundings are valid (not obstacles).
    
    Args:
        terrain (TerrainGenerator): Terrain generator
        start_pos (tuple): Starting position (x, y)
        radius (int): Radius around the starting position to clear
        
    Returns:
        tuple: Valid starting position
    """
    x, y = start_pos
    
    # First, generate the chunk containing the start position
    chunk_x = x // terrain.chunk_size
    chunk_y = y // terrain.chunk_size
    chunk = terrain.generate_chunk(chunk_x, chunk_y)
    
    # Clear obstacles around the starting position
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < terrain.width and 0 <= ny < terrain.height:
                # Force this position to have a valid elevation (not an obstacle)
                if terrain.is_obstacle(nx, ny):
                    # Get local coordinates within the chunk
                    local_x = nx % terrain.chunk_size
                    local_y = ny % terrain.chunk_size
                    local_chunk_x = nx // terrain.chunk_size
                    local_chunk_y = ny // terrain.chunk_size
                    
                    # If this position is in a different chunk, generate that chunk
                    if local_chunk_x != chunk_x or local_chunk_y != chunk_y:
                        local_chunk = terrain.generate_chunk(local_chunk_x, local_chunk_y)
                        # Set a valid elevation (middle of the range)
                        local_chunk[local_x, local_y] = terrain.max_elevation / 2
                    else:
                        # Set a valid elevation (middle of the range)
                        chunk[local_x, local_y] = terrain.max_elevation / 2
    
    return start_pos

def main():
    """Main function for the Mars Terrain Simulator."""
    # Parse command line arguments
    args = parse_args()
    
    # Create the GUI
    gui = GUI(fullscreen=args.fullscreen)
    
    # Display a splash screen with loading message
    gui.clear_screen()
    text = "Mars Terrain Simulator"
    gui.render_text(text, (gui.width // 2 - len(text) * 5, gui.height // 2 - 30), (255, 0, 0))
    text = "Generating terrain, please wait..."
    gui.render_text(text, (gui.width // 2 - len(text) * 5, gui.height // 2))
    gui.update()
    
    # Create the terrain generator (using smaller dimensions for testing)
    if args.test:
        terrain_width = 1000
        terrain_height = 1000
        chunk_size = 64
    else:
        terrain_width = args.width
        terrain_height = args.height
        chunk_size = args.chunk_size
    
    terrain = TerrainGenerator(
        width=terrain_width,
        height=terrain_height,
        max_elevation=args.max_elevation,
        chunk_size=chunk_size,
        seed=args.seed
    )
    
    # Set custom terrain parameters if provided
    obstacle_prob = args.obstacle_prob if args.obstacle_prob < 0.1 else 0.05
    terrain.obstacle_prob = obstacle_prob
    
    if args.scale:
        terrain.scale = args.scale
    
    # Create the pathfinder
    pathfinder = PathFinder(terrain)
    
    # Define a safe starting position (well away from the edges)
    start_pos = (50, 50)
    
    # Ensure the starting position is valid
    start_pos = ensure_valid_starting_position(terrain, start_pos)
    
    # Generate initial terrain around the starting point
    for x in range(-2, 3):
        for y in range(-2, 3):
            chunk_x = start_pos[0] // terrain.chunk_size + x
            chunk_y = start_pos[1] // terrain.chunk_size + y
            if chunk_x >= 0 and chunk_y >= 0:
                terrain.generate_chunk(chunk_x, chunk_y)
    
    # Create the player controller
    controller = PlayerController(terrain, pathfinder, gui, initial_pos=start_pos)
    
    # Create the camera
    camera = Camera(x=start_pos[0], y=start_pos[1], zoom=0.5)
    
    # Calculate minimap position in the upper right corner
    minimap_width = 200
    minimap_height = 200
    minimap_x = gui.width - minimap_width - 10
    minimap_y = 10
    
    # Create the minimap
    minimap = Minimap(
        width=terrain.width,
        height=terrain.height,
        terrain=terrain,
        position=(minimap_x, minimap_y),
        size=(minimap_width, minimap_height)
    )
    
    # Create the renderer with appropriate settings
    renderer = TerrainRenderer(gui.screen, terrain, block_size=5)
    
    # Create the input handler
    input_handler = InputHandler(gui, controller, camera, minimap)
    
    # Add initial status message
    gui.add_status_message("Welcome to Mars Terrain Simulator", (255, 255, 0))
    gui.add_status_message("Use WASD to move, K to toggle autopilot", (255, 255, 0))
    gui.add_status_message("Click on the minimap to set destination", (255, 255, 0))
    
    # Main simulation loop
    running = True
    while running:
        # Clear the screen
        gui.clear_screen()
        
        # Update camera
        camera.update()
        
        # Handle user input
        if input_handler.update():
            running = False
        
        # Update player and camera positions
        player_pos = controller.get_position()
        
        # Update the minimap
        minimap.update(player_pos, controller.path)
        
        # Render the terrain
        renderer.render(camera, player_pos, controller.path, controller.destination)
        
        # Draw the minimap
        minimap.draw(gui.screen)
        
        # Update and render HUD
        gui.update_status_messages()
        gui.render_status_messages()
        elevation = controller.get_elevation()
        if elevation < 0:
            # If the player is on an obstacle, move them to a valid position
            valid_neighbors = pathfinder.get_neighbors(player_pos)
            if valid_neighbors:
                # Move to the first valid position
                new_pos = valid_neighbors[0]
                controller.position = new_pos
                camera.set_position(new_pos[0], new_pos[1])
        gui.render_hud(player_pos, controller.get_elevation(), controller.autopilot_enabled)
        
        # Update the display
        gui.update()
        
        # Preload chunks around the player
        chunk_x = int(player_pos[0]) // terrain.chunk_size
        chunk_y = int(player_pos[1]) // terrain.chunk_size
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                terrain.generate_chunk(chunk_x + dx, chunk_y + dy)
        
        # Unload distant chunks to save memory
        terrain.unload_distant_chunks(int(player_pos[0]), int(player_pos[1]), 5)
    
    # Clean up
    gui.quit()
    return 0

if __name__ == '__main__':
    sys.exit(main()) 