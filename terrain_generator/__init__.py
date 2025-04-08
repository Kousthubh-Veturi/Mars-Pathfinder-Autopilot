"""
Mars Terrain Generator

High-performance terrain generation for Mars Terrain Simulator.
"""

__version__ = '1.0.0'

try:
    from .terrain_wrapper import TerrainGenerator
except ImportError:
    import sys
    print("Error: Failed to import the TerrainGenerator class.", file=sys.stderr)
    print("Make sure the C++ library 'libterrain_generator.so' is compiled and available.", file=sys.stderr)
    print("Run 'make' in the terrain_generator directory to build it.", file=sys.stderr)
    TerrainGenerator = None 