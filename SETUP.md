# Setup Guide - Mars Pathfinder Autopilot

This guide provides detailed instructions for setting up and running the Mars Pathfinder Autopilot simulation.

## Environment Setup

### Prerequisites

- Python 3.8+ (3.10+ recommended)
- C++ compiler:
  - **macOS**: Clang (installed with Xcode Command Line Tools)
  - **Linux**: GCC
  - **Windows**: MinGW-w64 or Visual Studio C++ Build Tools

### Virtual Environment

Create and activate a Python virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
.\venv\Scripts\activate
```

### Installing Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

### Building the C++ Module

The terrain generator uses high-performance C++ code that needs to be compiled:

```bash
python build.py
```

If you encounter compilation errors:

1. Make sure you have a compatible C++ compiler installed and in your PATH
2. On Windows, you may need to specify the compiler: `set VS90COMNTOOLS=C:\Path\to\your\compiler`
3. On macOS, you may need to install Xcode command line tools: `xcode-select --install`

## Running the Simulation

### Test Mode (Recommended for Development)

Run with smaller dimensions for faster startup and better performance:

```bash
python mars_terrain_simulator.py --test
```

### Full Scale Mode

For the complete Mars experience with full 15,000 x 15,000 terrain:

```bash
python mars_terrain_simulator.py
```

### Custom Configuration

Run with custom parameters for specific testing scenarios:

```bash
python mars_terrain_simulator.py --width 2000 --height 2000 --chunk-size 128 --obstacle-prob 0.03
```

## IDE Configuration

### Visual Studio Code

1. Install the Python and C/C++ extensions
2. Set your Python interpreter to the virtual environment
3. F5 to run the default configuration or use the Run menu

### PyCharm

1. Set the project interpreter to the virtual environment
2. Configure a run configuration for mars_terrain_simulator.py with appropriate arguments

## Troubleshooting

### Common Issues

1. **Black screen**: If you see a black screen when running, try using test mode to get a better view of what's happening.

2. **Memory issues**: If you encounter memory errors, try using a smaller world size or reducing the chunk size.

3. **"No module named terrain_generator"**: Make sure you've built the C++ module with `python build.py`.

4. **"libterrain_generator.so not found"**: The C++ module hasn't been built or can't be found. Check the build process output.

5. **Path issues**: If you're having path-related import errors, make sure you're running from the project's root directory.

## Post-Setup Verification

After setup, you should be able to:

1. Move around using WASD
2. See the HUD showing your position and elevation
3. Click on the minimap to set destinations
4. Toggle autopilot with the K key
5. Zoom in/out with the mouse wheel
6. Exit with ESC

If any of these functions aren't working, check the console for error messages. 