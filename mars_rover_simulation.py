import numpy as np
import matplotlib.pyplot as plt
import heapq
import random

# -------------------------------
# Simulation Parameters
# -------------------------------

GRID_WIDTH = 50          # Width of the terrain grid
GRID_HEIGHT = 50         # Height of the terrain grid
OBSTACLE_PROB = 0.2      # Probability that a cell is an obstacle (simulate rocks, craters, etc.)
ELEVATION_SCALE = 10     # Scale to multiply random elevation values
MAX_ELEVATION_DIFF = 3   # Maximum elevation difference allowed for easy traversal

# Start and goal coordinates on the grid
start = (0, 0)
goal = (GRID_HEIGHT - 1, GRID_WIDTH - 1)

# -------------------------------
# Terrain Generation
# -------------------------------

def generate_terrain(width, height, obstacle_prob, elevation_scale):
    """
    Generates a random terrain grid with elevation values and obstacles.
    Obstacles are marked by a value of -1. All other cells contain their elevation.
    """
    # Create a grid of random elevation values
    terrain = np.random.rand(height, width) * elevation_scale
    # Create obstacles: wherever random probability is less than obstacle_prob, mark as obstacle
    obstacle_mask = np.random.rand(height, width) < obstacle_prob
    terrain[obstacle_mask] = -1  # -1 represents an obstacle
    return terrain

# -------------------------------
# Visualization of the Terrain
# -------------------------------

def plot_terrain(terrain, path=None):
    """
    Plot the terrain grid. Optionally, plot a computed path over the terrain.
    Obstacles are shown in black. The path is highlighted if provided.
    """
    plt.figure(figsize=(8, 8))
    # Plot the elevation grid; use a colormap for elevation
    plt.imshow(terrain, cmap='terrain', origin='lower')
    plt.colorbar(label='Elevation')
    
    # Overlay obstacles in black
    obstacles = (terrain == -1)
    plt.imshow(obstacles, cmap='gray', alpha=0.5, origin='lower')
    
    # If a path is provided, plot it over the terrain
    if path:
        path_y, path_x = zip(*path)
        plt.plot(path_x, path_y, color='red', linewidth=2, label='Computed Path')
        plt.scatter([start[1], goal[1]], [start[0], goal[0]], c='blue', marker='o', s=100, label='Start/Goal')
        plt.legend()
    
    plt.title("Simulated Mars Terrain with Random Elevation and Obstacles")
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.show()

# -------------------------------
# Path Planning: A* Algorithm Implementation
# -------------------------------

def heuristic(a, b):
    """
    Compute the heuristic for A* (Manhattan distance is used for simplicity).
    More advanced heuristics may incorporate elevation differences and energy costs.
    """
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def get_neighbors(node, terrain):
    """
    Returns a list of neighboring cells that are within grid bounds and not obstacles.
    Diagonal movements are allowed; adjust for 4 or 8 connectivity as desired.
    """
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dx, dy in directions:
        nx = node[0] + dx
        ny = node[1] + dy
        if 0 <= nx < terrain.shape[0] and 0 <= ny < terrain.shape[1]:
            if terrain[nx, ny] != -1:  # If cell is not an obstacle
                neighbors.append((nx, ny))
    return neighbors

def compute_cost(current, neighbor, terrain):
    """
    Compute movement cost from the current cell to the neighbor cell.
    The cost includes base movement cost and additional cost for elevation changes.
    """
    base_cost = 1
    # Calculate the cost of elevation difference (simulate energy expenditure)
    elevation_current = terrain[current[0], current[1]]
    elevation_neighbor = terrain[neighbor[0], neighbor[1]]
    # If the elevation difference is too steep, assign a high cost (or disallow)
    if abs(elevation_current - elevation_neighbor) > MAX_ELEVATION_DIFF:
        return float('inf')
    elevation_cost = abs(elevation_current - elevation_neighbor)
    return base_cost + elevation_cost

def astar(terrain, start, goal):
    """
    A* algorithm implementation to compute the best path across the terrain.
    Returns a list of coordinates representing the path from start to goal.
    """
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}  # For path reconstruction

    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        current_priority, current = heapq.heappop(open_set)
        # If the goal is reached, reconstruct and return the path
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for neighbor in get_neighbors(current, terrain):
            tentative_g_score = g_score[current] + compute_cost(current, neighbor, terrain)
            # If the neighbor cannot be traversed easily, skip it
            if tentative_g_score == float('inf'):
                continue
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return None  # Return None if no path was found

# -------------------------------
# Rover Autopilot Simulation Loop
# -------------------------------

def simulate_rover(terrain, start, goal):
    """
    Simulate the rover autopilot by computing a path using the A* algorithm.
    This function also simulates the rover's progression along the computed path.
    """
    print("Starting rover simulation...")
    path = astar(terrain, start, goal)
    if path is None:
        print("No viable path found. Simulation aborted.")
        return
    print("Path found! Number of steps:", len(path))
    
    # Print each step as the rover progresses along the path
    for step_number, position in enumerate(path):
        # In a more advanced simulation, here you could simulate the rover's control commands,
        # sensor data fusion processing, and adjustments to changes in the terrain.
        print(f"Step {step_number + 1}: Rover at {position}")
        # Simulate a delay (for example, using time.sleep) if you wish to mimic real time
        # time.sleep(0.1)  # Uncomment this to simulate a real-time loop
    
    # Visualize the resulting path on the terrain
    plot_terrain(terrain, path)
    print("Simulation complete.")

# -------------------------------
# Main Execution
# -------------------------------

if __name__ == "__main__":
    # Generate the terrain and plot initial state (optional)
    terrain = generate_terrain(GRID_WIDTH, GRID_HEIGHT, OBSTACLE_PROB, ELEVATION_SCALE)
    print("Terrain generated. Starting point:", start, "Goal point:", goal)
    
    # Run the rover simulation (the autopilot computes the path and 'moves' the rover)
    simulate_rover(terrain, start, goal) 