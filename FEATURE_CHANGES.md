# Feature Implementation: Click to Mark Path with Minimal Elevation Changes

## Summary
Added a new feature allowing users to click anywhere on the main terrain view to mark a destination point. The system will automatically find the shortest path with minimal elevation changes from the rover's current position to the clicked point.

## Changes Made

### In `mars_terrain/control.py`:

1. Updated `InputHandler` class:
   - Added tracking of short clicks vs. drags
   - Added screen-to-world coordinate conversion for main view clicks
   - Implemented destination setting on main terrain view
   - Added validation to ensure clicked point is a valid destination

2. Enhanced `PlayerController` class:
   - Added GUI reference for displaying status messages
   - Updated `calculate_path` method to prioritize minimal elevation changes
   - Added calculation and display of total elevation changes along the path

### In `mars_terrain/terrain.py`:

1. Enhanced `PathFinder` class:
   - Added `elevation_weight` parameter (default: 1.5) to control emphasis on elevation changes
   - Updated `compute_cost` method to use this weight when calculating path costs
   - This ensures paths prefer more level routes over steep elevation changes

### In `mars_terrain/gui.py`:

1. Updated `TerrainRenderer` class:
   - Added display of destination marker on the main terrain view
   - Enhanced rendering to show a clear X marker at the destination point
   - Added visual indicators for the selected path

2. Updated `GUI` class:
   - Added instructions in the HUD about clicking to set destinations
   - Improved help text display

### In `mars_terrain_simulator.py`:

1. Updated controller initialization to include GUI reference
2. Updated renderer call to include destination information

## How to Use the Feature

1. **Click anywhere on the terrain** (not on the minimap) to set a destination point
2. The system will automatically calculate and display the optimal path with minimal elevation changes
3. A status message will show the total elevation changes along the path
4. Press **K** to toggle autopilot and follow the calculated path
5. The optimal path is shown in green on both the main view and minimap

## Technical Details

- The elevation-optimized pathfinding uses an enhanced A* algorithm
- Elevation differences are weighted 3x during pathfinding to prioritize level paths
- The system uses a dragging detection system to distinguish clicks from camera movements 