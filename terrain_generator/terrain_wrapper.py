import os
import ctypes
import numpy as np
from ctypes import c_int, c_float, c_double, c_bool, POINTER, c_void_p

# Path to shared library
_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libterrain_generator.so')

# Load the shared library
_lib = ctypes.CDLL(_lib_path)

# Define argument and return types for C functions
_lib.terrain_create.argtypes = [c_int, c_int, c_int, c_int, c_int]
_lib.terrain_create.restype = c_void_p

_lib.terrain_set_parameters.argtypes = [c_void_p, c_double, c_int, c_double, c_double, c_double]
_lib.terrain_set_parameters.restype = None

_lib.terrain_generate_chunk.argtypes = [c_void_p, c_int, c_int, POINTER(c_float)]
_lib.terrain_generate_chunk.restype = None

_lib.terrain_get_elevation.argtypes = [c_void_p, c_int, c_int]
_lib.terrain_get_elevation.restype = c_float

_lib.terrain_is_obstacle.argtypes = [c_void_p, c_int, c_int]
_lib.terrain_is_obstacle.restype = c_bool

_lib.terrain_unload_distant_chunks.argtypes = [c_void_p, c_int, c_int, c_int]
_lib.terrain_unload_distant_chunks.restype = None

_lib.terrain_clear_chunks.argtypes = [c_void_p]
_lib.terrain_clear_chunks.restype = None

_lib.terrain_destroy.argtypes = [c_void_p]
_lib.terrain_destroy.restype = None

class TerrainGenerator:
    def __init__(self, width=15000, height=15000, max_elevation=250, chunk_size=256, seed=None):
        """
        Initialize the terrain generator with the given parameters.
        
        Args:
            width (int): Width of the terrain in blocks
            height (int): Height of the terrain in blocks
            max_elevation (int): Maximum elevation difference
            chunk_size (int): Size of each terrain chunk
            seed (int): Random seed for terrain generation
        """
        if seed is None:
            import random
            seed = random.randint(0, 1000000)
        
        self.width = width
        self.height = height
        self.max_elevation = max_elevation
        self.chunk_size = chunk_size
        self.seed = seed
        
        # Create the C++ terrain generator
        self._terrain = _lib.terrain_create(width, height, max_elevation, chunk_size, seed)
        
        # Configure default terrain parameters
        self.scale = 0.01
        self.octaves = 6
        self.persistence = 0.5
        self.lacunarity = 2.0
        self.obstacle_prob = 0.2
        
        # Apply the default parameters
        self.set_parameters(self.scale, self.octaves, self.persistence, 
                           self.lacunarity, self.obstacle_prob)
        
        # Keep track of loaded chunks
        self.chunks = {}
    
    def __del__(self):
        """Clean up resources when object is destroyed."""
        if hasattr(self, '_terrain') and self._terrain:
            _lib.terrain_destroy(self._terrain)
            self._terrain = None
    
    def set_parameters(self, scale, octaves, persistence, lacunarity, obstacle_prob):
        """
        Set terrain generation parameters.
        
        Args:
            scale (float): Scale of noise features
            octaves (int): Number of noise layers
            persistence (float): How much each octave contributes to overall shape
            lacunarity (float): How much detail is added at each octave
            obstacle_prob (float): Probability of placing obstacles
        """
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.obstacle_prob = obstacle_prob
        
        _lib.terrain_set_parameters(
            self._terrain,
            c_double(scale),
            c_int(octaves),
            c_double(persistence),
            c_double(lacunarity),
            c_double(obstacle_prob)
        )
    
    def generate_chunk(self, chunk_x, chunk_y):
        """
        Generate a terrain chunk at the specified coordinates.
        
        Args:
            chunk_x (int): Chunk x coordinate
            chunk_y (int): Chunk y coordinate
            
        Returns:
            numpy.ndarray: Generated chunk data (2D array with elevation values)
        """
        # Check if chunk already exists in Python-side cache
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunks:
            return self.chunks[chunk_key]
        
        # Allocate memory for the chunk data
        chunk_data = np.zeros((self.chunk_size, self.chunk_size), dtype=np.float32)
        
        # Get C pointer to the chunk data
        chunk_data_ptr = chunk_data.ctypes.data_as(POINTER(c_float))
        
        # Generate the chunk data using C++ implementation
        _lib.terrain_generate_chunk(self._terrain, chunk_x, chunk_y, chunk_data_ptr)
        
        # Cache the chunk data
        self.chunks[chunk_key] = chunk_data
        
        return chunk_data
    
    def get_elevation(self, x, y):
        """
        Get the elevation at the specified world coordinates.
        
        Args:
            x (int): World x coordinate
            y (int): World y coordinate
            
        Returns:
            float: Elevation value at the specified position
        """
        return _lib.terrain_get_elevation(self._terrain, x, y)
    
    def is_obstacle(self, x, y):
        """
        Check if the specified position is an obstacle.
        
        Args:
            x (int): World x coordinate
            y (int): World y coordinate
            
        Returns:
            bool: True if the position is an obstacle, False otherwise
        """
        return _lib.terrain_is_obstacle(self._terrain, x, y)
    
    def get_visible_chunks(self, center_x, center_y, view_radius):
        """
        Get a list of visible chunk coordinates from the specified center point.
        
        Args:
            center_x (int): Center world x coordinate
            center_y (int): Center world y coordinate
            view_radius (int): View radius in chunks
            
        Returns:
            list: List of chunk coordinates (chunk_x, chunk_y)
        """
        # Calculate center chunk coordinates
        center_chunk_x = center_x // self.chunk_size
        center_chunk_y = center_y // self.chunk_size
        
        # Get all chunks within the view radius
        visible_chunks = []
        for dx in range(-view_radius, view_radius + 1):
            for dy in range(-view_radius, view_radius + 1):
                chunk_x = center_chunk_x + dx
                chunk_y = center_chunk_y + dy
                
                # Ensure chunk is within bounds
                if (0 <= chunk_x < self.width // self.chunk_size and 
                    0 <= chunk_y < self.height // self.chunk_size):
                    visible_chunks.append((chunk_x, chunk_y))
        
        return visible_chunks
    
    def unload_distant_chunks(self, center_x, center_y, max_view_radius):
        """
        Unload chunks that are too far from the specified center point.
        
        Args:
            center_x (int): Center world x coordinate
            center_y (int): Center world y coordinate
            max_view_radius (int): Maximum view radius in chunks
        """
        # Unload from C++ cache
        _lib.terrain_unload_distant_chunks(self._terrain, center_x, center_y, max_view_radius)
        
        # Also unload from Python-side cache
        center_chunk_x = center_x // self.chunk_size
        center_chunk_y = center_y // self.chunk_size
        
        chunks_to_remove = []
        for chunk_key in self.chunks:
            chunk_x, chunk_y = chunk_key
            
            # Calculate Manhattan distance
            dx = abs(chunk_x - center_chunk_x)
            dy = abs(chunk_y - center_chunk_y)
            distance = dx + dy
            
            if distance > max_view_radius:
                chunks_to_remove.append(chunk_key)
        
        # Remove chunks
        for chunk_key in chunks_to_remove:
            del self.chunks[chunk_key]
    
    def clear_chunks(self):
        """Clear all generated chunks from memory."""
        _lib.terrain_clear_chunks(self._terrain)
        self.chunks.clear() 