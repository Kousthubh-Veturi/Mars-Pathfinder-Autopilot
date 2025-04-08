# First-Person Mode for Mars Terrain Simulator

## Overview

The Mars Terrain Simulator now includes a first-person mode that allows you to experience the Martian landscape from the rover's perspective. This feature provides an immersive way to navigate and explore the terrain, with enhanced movement capabilities allowing the rover to climb or jump up to 2 blocks in height.

## Key Features

1. **Toggle View Mode**: Press `R` to switch between top-down and first-person views
2. **Enhanced Movement**:
   - In first-person mode, the rover can climb or jump up to 2 blocks in height
   - Movement speed is capped at 5 blocks per second for realistic exploration
   - WASD keys provide directional control relative to the rover's facing direction

3. **Mouse Look Control**:
   - Left-click to lock/unlock mouse for camera rotation
   - Move the mouse to look around in first-person mode
   - ESC releases mouse control without exiting the application

4. **Autopilot in First-Person**:
   - Press `K` to toggle autopilot mode
   - Watch the rover navigate the terrain automatically in first-person view
   - The path is visualized with green markers

## Movement Controls

In first-person mode, the controls are:

| Control | Action |
|---------|--------|
| W | Move forward |
| S | Move backward (slower than forward) |
| A | Strafe left |
| D | Strafe right |
| Mouse | Look around (when mouse is locked) |
| Left-click | Lock/unlock mouse control |
| R | Toggle back to top-down view |
| K | Toggle autopilot |
| ESC | Release mouse lock (or exit if mouse already unlocked) |

## Technical Details

The first-person mode implements:

1. **Raycasting Renderer**: Efficiently renders the 3D perspective of the terrain
2. **Realistic Physics**: The rover can climb gradual slopes and jump up to 2 blocks
3. **Atmosphere Effects**: Distance fog and sky gradient to enhance immersion
4. **Path Visualization**: Destination and path markers are visible in 3D space
5. **Integrated HUD**: Maintains the same core information as top-down view

## Tips for Using First-Person Mode

- First-person mode is excellent for exploring the details of the Martian terrain
- Use the autopilot for long journeys while enjoying the view
- The minimap remains visible to help with overall navigation
- First-person mode can make it easier to navigate rough terrain
- When encountering steep cliffs, remember the 2-block climbing limit
- Lock the mouse (left-click) for precise camera control
- Press ESC to release the mouse cursor without exiting the application

## Implementation Notes

The first-person mode is implemented using:

- Customized raycasting algorithm optimized for performance
- Frame-rate independent movement for consistent experience
- Smooth camera interpolation for fluid motion
- Integration with the existing pathfinding system
- Adaptive rendering quality based on distance 