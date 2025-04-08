import numpy as np
import heapq
import random
from collections import defaultdict

# Check if the C++ terrain generator is available
try:
    from terrain_generator import TerrainGenerator as CppTerrainGenerator
    USING_CPP = True
except ImportError:
    USING_CPP = False
    print("C++ terrain generator not available. Using slower Python implementation.")
    print("For better performance, build the C++ terrain generator.")


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
        self.width = width
        self.height = height
        self.max_elevation = max_elevation
        self.chunk_size = chunk_size
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        
        # Configure terrain generation parameters
        self.scale = 0.01  # Controls the scale of the terrain features
        self.octaves = 6   # Number of noise layers
        self.persistence = 0.5  # How much each octave contributes to the overall shape
        self.lacunarity = 2.0   # How much detail is added at each octave
        self.obstacle_prob = 0.2  # Probability of placing an obstacle
        
        # Use the C++ implementation if available
        if USING_CPP:
            self.cpp_terrain = CppTerrainGenerator(
                width, height, max_elevation, chunk_size, self.seed
            )
            self.cpp_terrain.set_parameters(
                self.scale, self.octaves, self.persistence, 
                self.lacunarity, self.obstacle_prob
            )
            # Dictionary to store references to generated chunks (just for API compatibility)
            self.chunks = {}
        else:
            # Initialize noise generator
            try:
                import opensimplex
                opensimplex.seed(self.seed)
                self.noise_gen = opensimplex.noise2
            except ImportError:
                import noise
                self.noise_gen = lambda x, y: noise.snoise2(x, y, octaves=self.octaves, 
                                                         persistence=self.persistence, 
                                                         lacunarity=self.lacunarity)
            
            # Dictionary to store generated chunks
            self.chunks = {}
        
    def generate_chunk(self, chunk_x, chunk_y):
        """
        Generate a terrain chunk at the specified coordinates.
        
        Args:
            chunk_x (int): Chunk x coordinate
            chunk_y (int): Chunk y coordinate
            
        Returns:
            numpy.ndarray: Generated chunk data (2D array with elevation values)
        """
        # Check if using C++ implementation
        if USING_CPP:
            return self.cpp_terrain.generate_chunk(chunk_x, chunk_y)
        
        # Python implementation
        # Check if chunk already exists
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunks:
            return self.chunks[chunk_key]
        
        # Create a new chunk
        chunk = np.zeros((self.chunk_size, self.chunk_size))
        
        # Calculate the absolute position of the chunk
        abs_x = chunk_x * self.chunk_size
        abs_y = chunk_y * self.chunk_size
        
        # Generate elevation values using noise
        for x in range(self.chunk_size):
            for y in range(self.chunk_size):
                # Calculate absolute coordinates
                world_x = abs_x + x
                world_y = abs_y + y
                
                # Generate elevation using multiple octaves of noise
                elevation = 0
                amplitude = 1
                frequency = 1
                
                for i in range(self.octaves):
                    nx = world_x * self.scale * frequency
                    ny = world_y * self.scale * frequency
                    
                    # Add noise contribution for this octave
                    elevation += self.noise_gen(nx, ny) * amplitude
                    
                    # Update amplitude and frequency for next octave
                    amplitude *= self.persistence
                    frequency *= self.lacunarity
                
                # Normalize the elevation to be between 0 and max_elevation
                elevation = (elevation + 1) / 2  # Convert from [-1, 1] to [0, 1]
                elevation = elevation * self.max_elevation
                
                # Randomly place obstacles (represented by -1)
                if random.random() < self.obstacle_prob:
                    chunk[x, y] = -1  # -1 represents an obstacle
                else:
                    chunk[x, y] = elevation
        
        # Store the generated chunk
        self.chunks[chunk_key] = chunk
        return chunk
    
    def get_elevation(self, x, y):
        """
        Get the elevation at the specified world coordinates.
        
        Args:
            x (int): World x coordinate
            y (int): World y coordinate
            
        Returns:
            float: Elevation value at the specified position
        """
        # Check if using C++ implementation
        if USING_CPP:
            return self.cpp_terrain.get_elevation(int(x), int(y))
        
        # Python implementation
        # Ensure coordinates are within the world bounds
        if 0 <= x < self.width and 0 <= y < self.height:
            # Calculate chunk coordinates
            chunk_x = x // self.chunk_size
            chunk_y = y // self.chunk_size
            
            # Calculate local coordinates within the chunk
            local_x = int(x % self.chunk_size)
            local_y = int(y % self.chunk_size)
            
            # Generate or retrieve the chunk
            chunk = self.generate_chunk(chunk_x, chunk_y)
            
            # Return the elevation at the specified position
            return chunk[local_x, local_y]
        else:
            # Return a border value for out-of-bounds coordinates
            return -1  # Treat out-of-bounds as obstacles
    
    def is_obstacle(self, x, y):
        """
        Check if the specified position is an obstacle.
        
        Args:
            x (int): World x coordinate
            y (int): World y coordinate
            
        Returns:
            bool: True if the position is an obstacle, False otherwise
        """
        # Check if using C++ implementation
        if USING_CPP:
            return self.cpp_terrain.is_obstacle(int(x), int(y))
        
        # Python implementation
        elevation = self.get_elevation(x, y)
        return elevation == -1
    
    def get_visible_chunks(self, center_x, center_y, view_radius):
        """
        Get a list of chunks visible from the specified center point.
        
        Args:
            center_x (int): Center world x coordinate
            center_y (int): Center world y coordinate
            view_radius (int): View radius in chunks
            
        Returns:
            list: List of chunk coordinates (chunk_x, chunk_y)
        """
        # Check if using C++ implementation
        if USING_CPP:
            return self.cpp_terrain.get_visible_chunks(int(center_x), int(center_y), view_radius)
        
        # Python implementation
        # Calculate center chunk coordinates
        center_chunk_x = center_x // self.chunk_size
        center_chunk_y = center_y // self.chunk_size
        
        # Get all chunks within the view radius
        visible_chunks = []
        
        for dx in range(-view_radius, view_radius + 1):
            for dy in range(-view_radius, view_radius + 1):
                chunk_x = center_chunk_x + dx
                chunk_y = center_chunk_y + dy
                
                # Ensure chunk is within world bounds
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
        # Check if using C++ implementation
        if USING_CPP:
            self.cpp_terrain.unload_distant_chunks(int(center_x), int(center_y), max_view_radius)
            return
        
        # Python implementation
        # Calculate center chunk coordinates
        center_chunk_x = center_x // self.chunk_size
        center_chunk_y = center_y // self.chunk_size
        
        # Get all loaded chunks
        chunks_to_remove = []
        
        for chunk_key in self.chunks:
            chunk_x, chunk_y = chunk_key
            
            # Calculate distance to center chunk
            dx = abs(chunk_x - center_chunk_x)
            dy = abs(chunk_y - center_chunk_y)
            
            # Use Manhattan distance for simplicity
            distance = dx + dy
            
            # Unload chunks that are too far away
            if distance > max_view_radius:
                chunks_to_remove.append(chunk_key)
        
        # Remove chunks
        for chunk_key in chunks_to_remove:
            del self.chunks[chunk_key]


class PathFinder:
    def __init__(self, terrain):
        """
        Initialize the pathfinder with the given terrain.
        
        Args:
            terrain (TerrainGenerator): Terrain generator instance
        """
        self.terrain = terrain
        
    def heuristic(self, a, b):
        """
        Compute the heuristic for A* (Manhattan distance).
        
        Args:
            a (tuple): First position (x, y)
            b (tuple): Second position (x, y)
            
        Returns:
            float: Heuristic value
        """
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)
    
    def get_neighbors(self, node):
        """
        Get all traversable neighboring positions.
        
        Args:
            node (tuple): Current position (x, y)
            
        Returns:
            list: List of traversable neighboring positions
        """
        x, y = node
        neighbors = []
        
        # Consider 8 directions (including diagonals)
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal directions
            (1, 1), (1, -1), (-1, -1), (-1, 1)  # Diagonal directions
        ]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check if the position is within bounds and not an obstacle
            if (0 <= nx < self.terrain.width and 0 <= ny < self.terrain.height and 
                not self.terrain.is_obstacle(nx, ny)):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def compute_cost(self, current, neighbor):
        """
        Compute the cost of moving from current to neighbor.
        
        Args:
            current (tuple): Current position (x, y)
            neighbor (tuple): Neighbor position (x, y)
            
        Returns:
            float: Movement cost
        """
        # Base cost for movement
        base_cost = 1.0
        
        # Add additional cost for diagonal movement
        cx, cy = current
        nx, ny = neighbor
        if cx != nx and cy != ny:  # Diagonal movement
            base_cost = 1.4  # sqrt(2)
        
        # Add cost for elevation difference
        elevation_current = self.terrain.get_elevation(cx, cy)
        elevation_neighbor = self.terrain.get_elevation(nx, ny)
        
        if elevation_current == -1 or elevation_neighbor == -1:
            return float('inf')  # Cannot move to/from obstacles
        
        elevation_diff = abs(elevation_current - elevation_neighbor)
        
        # If elevation difference is too steep, make it very costly
        if elevation_diff > self.terrain.max_elevation / 10:
            return base_cost + elevation_diff * 10
        
        return base_cost + elevation_diff
    
    def a_star(self, start, goal):
        """
        Find the shortest path using A* algorithm.
        
        Args:
            start (tuple): Start position (x, y)
            goal (tuple): Goal position (x, y)
            
        Returns:
            list: List of positions forming the path, or None if no path is found
        """
        # Check if start or goal is an obstacle
        if (self.terrain.is_obstacle(start[0], start[1]) or 
            self.terrain.is_obstacle(goal[0], goal[1])):
            return None
        
        # Open set for A* (priority queue)
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        # Dictionary to store the best path
        came_from = {}
        
        # Dictionary to store the cost to reach each node
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        # Dictionary to store the estimated total cost
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self.heuristic(start, goal)
        
        # Set to keep track of nodes in the open set (for faster lookup)
        open_set_hash = {start}
        
        while open_set:
            # Get the node with the lowest f_score
            _, current = heapq.heappop(open_set)
            open_set_hash.remove(current)
            
            # If we reached the goal, reconstruct the path
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            # Check all neighbors
            for neighbor in self.get_neighbors(current):
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + self.compute_cost(current, neighbor)
                
                # If this path is better than the previous one
                if tentative_g_score < g_score[neighbor]:
                    # Update the path
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    
                    # Add to open set if not already there
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # No path found
        return None 