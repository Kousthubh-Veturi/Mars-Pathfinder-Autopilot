# Space Systems - Mars Pathfinder Autopilot in Randomly Generated Terrain

An interactive Mars terrain simulator with procedural terrain generation and autonomous pathfinding capabilities. This simulator features a vast, Minecraft-style Mars terrain spanning 15,000 × 15,000 blocks with up to 250 blocks of elevation change.

## High-Performance Architecture

This simulator uses a hybrid approach combining Python and C++ for optimal performance:

- **C++ Terrain Generator**: Procedural terrain generation is implemented in C++ for maximum speed
- **Python Interface**: The user interface, controls, and simulation logic are implemented in Python
- **A* Pathfinding**: Intelligent autopilot navigates the complex Mars terrain using A* search algorithm

## Features

- Vast procedurally generated Mars-like terrain (15,000 x 15,000 blocks)
- Interactive minimap for navigation and destination selection
- Dual control modes:
  - Manual control using WASD keys
  - Autopilot navigation (toggle with K key)
- A* pathfinding algorithm for optimal path planning
- Chunk-based terrain generation for efficient memory usage
- Dynamic lighting system for enhanced visuals
- Efficient path visualization

## Running the Simulation

### Setting Up 

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   .\venv\Scripts\activate
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Build the C++ terrain generator:
   ```bash
   python build.py
   ```

### Running

Run the simulation in test mode (recommended for better performance):
```bash
python mars_terrain_simulator.py --test
```

Or run the full-scale simulation:
```bash
python mars_terrain_simulator.py
```

### Controls

- **WASD** - Move the rover
- **K** - Toggle autopilot mode
- **Mouse click on minimap** - Set destination marker
- **Mouse wheel** - Zoom in/out
- **Mouse drag** - Move the camera
- **ESC** - Exit the simulation

## Command-Line Options

```bash
python mars_terrain_simulator.py [options]
```

Options:
- `--width WIDTH` - Width of the terrain in blocks (default: 15000)
- `--height HEIGHT` - Height of the terrain in blocks (default: 15000)
- `--max-elevation MAX_ELEVATION` - Maximum elevation in blocks (default: 250)
- `--chunk-size CHUNK_SIZE` - Size of terrain chunks (default: 256)
- `--seed SEED` - Random seed for terrain generation
- `--fullscreen` - Run in fullscreen mode
- `--scale SCALE` - Terrain scale factor (default: 0.01)
- `--obstacle-prob OBSTACLE_PROB` - Probability of obstacles (default: 0.05)
- `--test` - Run in test mode with smaller world size (1000x1000)

## Technical Details

The simulation is built with:
- Procedural terrain generation using noise algorithms
- Efficient chunk-based world loading/unloading
- Dynamic lighting system for realistic terrain shading
- A* pathfinding with elevation and obstacle cost consideration
- Python/C++ integration for maximum performance

## Requirements

To run these simulations, you need the following:

### Python Packages
- numpy
- matplotlib
- pygame
- opensimplex
- noise
- cffi (for C++ integration)

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```

### C++ Compiler Requirements
To build the high-performance C++ terrain generator:
- **Linux/macOS**: GCC or Clang with C++14 support
- **Windows**: MinGW-w64 or Visual Studio with C++14 support

## Building the Terrain Generator

Before running the simulation, build the C++ terrain generator:

```bash
python build.py
```

This will compile the C++ code into a shared library that Python can use.

## Basic Mars Rover Simulation

The basic simulation creates a simple 2D grid-based Mars-like terrain and implements pathfinding using the A* algorithm.

### Usage

```bash
python mars_rover_simulation.py
```

The script will:
- Generate a random Mars-like terrain with obstacles
- Compute a path from the start point (0,0) to the goal point (bottom-right corner)
- Display the rover's progress in the terminal
- Generate a visualization of the terrain and the computed path

## Full-Screen Mars Terrain Simulator

The full-screen simulator creates a vast, Minecraft-style Mars terrain spanning 15,000 × 15,000 blocks with up to 250 blocks of elevation change. It features a fully interactive interface with both manual and autopilot navigation.

### Features

- Vast procedurally generated Mars-like terrain (15,000 x 15,000 blocks)
- Interactive minimap for navigation and destination selection
- Dual control modes:
  - Manual control using WASD keys
  - Autopilot navigation (toggle with K key)
- A* pathfinding algorithm for optimal path planning
- Chunk-based terrain generation for efficient memory usage
- Dynamic loading and unloading of terrain chunks
- Camera controls with zoom and smooth movement

### Command-Line Options

```bash
python mars_terrain_simulator.py [options]
```

Options:
- `--width WIDTH` - Width of the terrain in blocks (default: 15000)
- `--height HEIGHT` - Height of the terrain in blocks (default: 15000)
- `--max-elevation MAX_ELEVATION` - Maximum elevation in blocks (default: 250)
- `--chunk-size CHUNK_SIZE` - Size of terrain chunks (default: 256)
- `--seed SEED` - Random seed for terrain generation
- `--fullscreen` - Run in fullscreen mode
- `--scale SCALE` - Terrain scale factor (default: 0.01)
- `--obstacle-prob OBSTACLE_PROB` - Probability of obstacles (default: 0.05)
- `--test` - Run in test mode with smaller world size (1000x1000)

For a smaller test environment:

```bash
python mars_terrain_simulator.py --test
```

### Controls

- **WASD** - Move the rover
- **K** - Toggle autopilot mode
- **Mouse click on minimap** - Set destination marker
- **Mouse wheel** - Zoom in/out
- **Mouse drag** - Move the camera
- **ESC** - Exit the simulation

## Performance Considerations

The full Mars Terrain Simulator is designed to handle the vast 15,000 x 15,000 block world efficiently:

1. **C++ Terrain Generation**: The most computationally intensive part, terrain generation, is offloaded to C++ for maximum performance.
2. **Chunk-Based Loading**: Only a small portion of the world is loaded in memory at any time, with distant chunks unloaded automatically.
3. **Optimized Rendering**: Only the visible portion of the terrain is rendered, with level-of-detail adjustments based on zoom level.
4. **Memory Management**: The system carefully manages memory to prevent leaks during long play sessions.

If you experience performance issues:
- Use the `--test` flag for a smaller world size
- Decrease the chunk size (e.g., `--chunk-size 128`)
- Reduce obstacle probability (e.g., `--obstacle-prob 0.03`)
- Adjust the scale for less detailed terrain (e.g., `--scale 0.02`)

## Troubleshooting

- **Black screen or no display**: Make sure pygame is properly installed and your display supports the resolution.
- **Slow performance**: Use the `--test` flag for a smaller world or reduce chunk size.
- **C++ compilation errors**: Make sure you have a compatible C++ compiler installed. On Windows, install MinGW or Visual Studio.
- **"Invalid starting position"**: The simulation now automatically fixes invalid starting positions.

## Extensions

These simulations can be extended in several ways:
- Add simulated sensor noise
- Implement dynamic obstacles
- Create more sophisticated terrain generation algorithms
- Add energy consumption modeling
- Implement more advanced visualization

Enjoy exploring the simulated Mars terrain with your autonomous rover! 