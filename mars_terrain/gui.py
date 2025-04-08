import pygame
import numpy as np
import os
import math

class Camera:
    def __init__(self, x=0, y=0, zoom=1.0):
        """
        Initialize the camera with the given parameters.
        
        Args:
            x (int): Initial x position
            y (int): Initial y position
            zoom (float): Initial zoom level
        """
        self.x = x
        self.y = y
        self.zoom = zoom
        self.target_x = x
        self.target_y = y
        self.target_zoom = zoom
        self.smooth_factor = 0.1  # Camera smoothing factor
    
    def update(self):
        """Update camera position and zoom with smooth interpolation."""
        # Smooth camera movement
        self.x += (self.target_x - self.x) * self.smooth_factor
        self.y += (self.target_y - self.y) * self.smooth_factor
        self.zoom += (self.target_zoom - self.zoom) * self.smooth_factor
    
    def set_position(self, x, y):
        """Set the target position for the camera."""
        self.target_x = x
        self.target_y = y
    
    def set_zoom(self, zoom):
        """Set the target zoom level for the camera."""
        self.target_zoom = max(0.1, min(zoom, 5.0))
    
    def move(self, dx, dy):
        """Move the camera by the specified amount."""
        self.target_x += dx
        self.target_y += dy
    
    def zoom_in(self, factor=1.1):
        """Zoom in by the specified factor."""
        self.set_zoom(self.target_zoom * factor)
    
    def zoom_out(self, factor=0.9):
        """Zoom out by the specified factor."""
        self.set_zoom(self.target_zoom * factor)
    
    def world_to_screen(self, world_x, world_y, screen_width, screen_height):
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.x) * self.zoom + screen_width / 2
        screen_y = (world_y - self.y) * self.zoom + screen_height / 2
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y, screen_width, screen_height):
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - screen_width / 2) / self.zoom + self.x
        world_y = (screen_y - screen_height / 2) / self.zoom + self.y
        return world_x, world_y


class FirstPersonCamera:
    def __init__(self, position=(0, 0), direction=0, max_elevation=250):
        """
        Initialize the first-person camera.
        
        Args:
            position (tuple): Initial position (x, y)
            direction (float): Initial direction in radians (0 = positive x-axis)
            max_elevation (int): Maximum terrain elevation for vertical positioning
        """
        self.position = position
        self.direction = direction  # Direction in radians
        self.vertical_angle = 0     # Vertical angle in radians
        self.max_elevation = max_elevation
        self.height_offset = 5      # Camera height above terrain
        
        # Field of view (in radians)
        self.horizontal_fov = math.radians(90)
        self.vertical_fov = math.radians(60)
        
        # View distance
        self.view_distance = 50
        
        # Camera movement smoothing
        self.target_position = position
        self.target_direction = direction
        self.target_vertical_angle = 0
        self.smooth_factor = 0.2
    
    def update(self):
        """Update camera position and orientation with smooth interpolation."""
        # Smooth position movement
        self.position = (
            self.position[0] + (self.target_position[0] - self.position[0]) * self.smooth_factor,
            self.position[1] + (self.target_position[1] - self.position[1]) * self.smooth_factor
        )
        
        # Smooth direction rotation
        angle_diff = self.target_direction - self.direction
        # Handle angle wrapping
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        self.direction += angle_diff * self.smooth_factor
        
        # Wrap direction between 0 and 2*pi
        self.direction %= 2 * math.pi
        
        # Smooth vertical angle
        self.vertical_angle += (self.target_vertical_angle - self.vertical_angle) * self.smooth_factor
        
        # Clamp vertical angle to prevent looking too far up or down
        self.vertical_angle = max(-math.pi/3, min(math.pi/3, self.vertical_angle))
    
    def set_position(self, x, y, terrain):
        """
        Set the target position and adjust height based on terrain.
        
        Args:
            x (float): Target x position
            y (float): Target y position
            terrain (TerrainGenerator): Terrain generator to get elevation
        """
        self.target_position = (x, y)
        
        # Get current elevation at the camera position
        elevation = terrain.get_elevation(int(x), int(y))
        if elevation < 0:  # Handle obstacles
            elevation = 0
        
        # Camera height is terrain elevation plus offset
        self.height = elevation + self.height_offset
    
    def set_direction(self, direction):
        """
        Set the target horizontal camera direction.
        
        Args:
            direction (float): Target direction in radians
        """
        self.target_direction = direction
    
    def set_vertical_angle(self, angle):
        """
        Set the target vertical camera angle.
        
        Args:
            angle (float): Target vertical angle in radians
        """
        self.target_vertical_angle = max(-math.pi/3, min(math.pi/3, angle))
    
    def rotate(self, delta_x, delta_y):
        """
        Rotate the camera based on mouse movement.
        
        Args:
            delta_x (float): Horizontal mouse movement
            delta_y (float): Vertical mouse movement
        """
        # Rotate horizontally (around y-axis)
        self.target_direction -= delta_x * 0.005
        
        # Wrap direction between 0 and 2*pi
        self.target_direction %= 2 * math.pi
        
        # Rotate vertically (around x-axis)
        self.target_vertical_angle -= delta_y * 0.005
        
        # Clamp vertical angle
        self.target_vertical_angle = max(-math.pi/3, min(math.pi/3, self.target_vertical_angle))
    
    def get_view_ray(self, screen_x, screen_y, screen_width, screen_height):
        """
        Get a ray from the camera to the world for a screen pixel.
        
        Args:
            screen_x (int): Screen x coordinate
            screen_y (int): Screen y coordinate
            screen_width (int): Screen width
            screen_height (int): Screen height
            
        Returns:
            tuple: Ray direction vector (x, y)
        """
        # Calculate the normalized device coordinates (-1 to 1)
        ndc_x = (2.0 * screen_x / screen_width) - 1.0
        ndc_y = 1.0 - (2.0 * screen_y / screen_height)
        
        # Convert to angles
        angle_h = self.direction + ndc_x * (self.horizontal_fov / 2)
        angle_v = self.vertical_angle + ndc_y * (self.vertical_fov / 2)
        
        # Calculate ray direction vector
        ray_x = math.cos(angle_h) * math.cos(angle_v)
        ray_y = math.sin(angle_h) * math.cos(angle_v)
        
        return (ray_x, ray_y)


class TerrainColors:
    """Color palette for different terrain elevations and features."""
    
    # Define colors for different elevation ranges
    OBSTACLE = (40, 40, 40)        # Dark gray for obstacles
    VERY_LOW = (173, 139, 115)     # Sandy brown for very low elevations
    LOW = (194, 162, 126)          # Light brown for low elevations
    MEDIUM_LOW = (210, 180, 140)   # Tan for medium-low elevations
    MEDIUM = (222, 192, 158)       # Beige for medium elevations
    MEDIUM_HIGH = (200, 170, 120)  # Darker tan for medium-high elevations
    HIGH = (180, 150, 100)         # Darker brown for high elevations
    VERY_HIGH = (160, 130, 80)     # Darkest brown for very high elevations
    
    @staticmethod
    def get_color(elevation, max_elevation):
        """
        Get the color for the given elevation.
        
        Args:
            elevation (float): Elevation value
            max_elevation (float): Maximum elevation
            
        Returns:
            tuple: RGB color values (r, g, b)
        """
        if elevation < 0:
            return TerrainColors.OBSTACLE
        
        # Normalize elevation to range [0, 1]
        normalized = elevation / max_elevation
        
        # Determine color based on normalized elevation
        if normalized < 0.1:
            return TerrainColors.VERY_LOW
        elif normalized < 0.25:
            return TerrainColors.LOW
        elif normalized < 0.4:
            return TerrainColors.MEDIUM_LOW
        elif normalized < 0.6:
            return TerrainColors.MEDIUM
        elif normalized < 0.75:
            return TerrainColors.MEDIUM_HIGH
        elif normalized < 0.9:
            return TerrainColors.HIGH
        else:
            return TerrainColors.VERY_HIGH
    
    @staticmethod
    def get_shaded_color(color, shade_factor):
        """
        Apply shading to a color.
        
        Args:
            color (tuple): Base RGB color
            shade_factor (float): Shading factor (0.0 to 1.0)
            
        Returns:
            tuple: Shaded RGB color
        """
        r, g, b = color
        r = max(0, min(255, int(r * shade_factor)))
        g = max(0, min(255, int(g * shade_factor)))
        b = max(0, min(255, int(b * shade_factor)))
        return (r, g, b)


class Minimap:
    def __init__(self, width, height, terrain, position=(0, 0), size=(200, 200)):
        """
        Initialize the minimap.
        
        Args:
            width (int): World width
            height (int): World height
            terrain (TerrainGenerator): Terrain generator instance
            position (tuple): Position of the minimap on screen (x, y)
            size (tuple): Size of the minimap (width, height)
        """
        self.world_width = width
        self.world_height = height
        self.terrain = terrain
        self.position = position
        self.size = size
        self.x_offset, self.y_offset = position
        self.width, self.height = size
        
        # Create the minimap surface
        self.surface = pygame.Surface(size)
        
        # Destination marker
        self.destination = None
        self.player_pos = (0, 0)
        self.path = None
        
        # Generate the minimap at a lower resolution
        self.generate_minimap()
    
    def generate_minimap(self):
        """Generate a low-resolution version of the terrain for the minimap."""
        # Clear the surface
        self.surface.fill((0, 0, 0))
        
        # Calculate the scale factor
        scale_x = self.width / self.world_width
        scale_y = self.height / self.world_height
        
        # Sample the terrain at regular intervals to generate the minimap
        sample_size = max(1, min(self.world_width // self.width, self.world_height // self.height))
        
        for x in range(0, self.world_width, sample_size):
            for y in range(0, self.world_height, sample_size):
                # Get the elevation at this position
                elevation = self.terrain.get_elevation(x, y)
                
                # Calculate the color based on elevation
                color = TerrainColors.get_color(elevation, self.terrain.max_elevation)
                
                # Calculate the position on the minimap
                minimap_x = int(x * scale_x)
                minimap_y = int(y * scale_y)
                
                # Draw a pixel (or small rect) at this position
                size = max(1, int(scale_x * sample_size))
                pygame.draw.rect(self.surface, color, (minimap_x, minimap_y, size, size))
    
    def update(self, player_pos, path=None):
        """
        Update the minimap with the player's position and path.
        
        Args:
            player_pos (tuple): Player's position (x, y)
            path (list): List of path waypoints
        """
        self.player_pos = player_pos
        self.path = path
    
    def set_destination(self, screen_x, screen_y):
        """
        Set the destination marker at the given screen coordinates.
        
        Args:
            screen_x (int): Screen x coordinate
            screen_y (int): Screen y coordinate
            
        Returns:
            tuple: World coordinates of the destination
        """
        # Check if the click is within the minimap bounds
        if (self.x_offset <= screen_x <= self.x_offset + self.width and
            self.y_offset <= screen_y <= self.y_offset + self.height):
            
            # Convert minimap coordinates to world coordinates
            map_x = screen_x - self.x_offset
            map_y = screen_y - self.y_offset
            
            world_x = int(map_x * (self.world_width / self.width))
            world_y = int(map_y * (self.world_height / self.height))
            
            # Set the destination
            self.destination = (world_x, world_y)
            return (world_x, world_y)
        
        return None
    
    def draw(self, screen):
        """
        Draw the minimap on the screen.
        
        Args:
            screen (pygame.Surface): Screen surface to draw on
        """
        # Draw the minimap background
        screen.blit(self.surface, self.position)
        
        # Draw the border
        pygame.draw.rect(screen, (255, 255, 255), 
                         (self.x_offset, self.y_offset, self.width, self.height), 2)
        
        # Calculate the player's position on the minimap
        px = int(self.player_pos[0] * (self.width / self.world_width)) + self.x_offset
        py = int(self.player_pos[1] * (self.height / self.world_height)) + self.y_offset
        
        # Draw the player's position
        pygame.draw.circle(screen, (0, 0, 255), (px, py), 3)
        
        # Draw the destination marker if set
        if self.destination:
            dx = int(self.destination[0] * (self.width / self.world_width)) + self.x_offset
            dy = int(self.destination[1] * (self.height / self.world_height)) + self.y_offset
            pygame.draw.circle(screen, (255, 0, 0), (dx, dy), 3)
        
        # Draw the path if available
        if self.path:
            points = []
            for p in self.path:
                x = int(p[0] * (self.width / self.world_width)) + self.x_offset
                y = int(p[1] * (self.height / self.world_height)) + self.y_offset
                points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(screen, (0, 255, 0), False, points, 2)


class TerrainRenderer:
    def __init__(self, screen, terrain, block_size=10, view_distance=1000):
        """
        Initialize the terrain renderer.
        
        Args:
            screen (pygame.Surface): Screen surface to draw on
            terrain (TerrainGenerator): Terrain generator instance
            block_size (int): Size of each block in pixels
            view_distance (int): Maximum view distance in blocks
        """
        self.screen = screen
        self.terrain = terrain
        self.block_size = block_size
        self.view_distance = view_distance
        
        # Create a color cache to avoid recalculating colors
        self.color_cache = {}
        
        # For improved visual quality
        self.use_lighting = True
        self.light_direction = (-1, -1)  # Light coming from top-left
        self.ambient_light = 0.5  # Amount of ambient light (0.0 to 1.0)
        
        # Sky color for first-person mode background
        self.sky_color = (135, 206, 235)  # Light blue
        self.horizon_color = (225, 225, 200)  # Light yellow/tan
    
    def get_color(self, elevation, x, y, neighbors=None):
        """
        Get the color for the given elevation, using a cache for efficiency.
        Apply lighting if enabled.
        
        Args:
            elevation (float): Elevation value
            x (int): X coordinate for calculating shading
            y (int): Y coordinate for calculating shading
            neighbors (dict): Dictionary of neighbor elevations for lighting
            
        Returns:
            tuple: RGB color values (r, g, b)
        """
        # Get base color for this elevation
        if elevation not in self.color_cache:
            self.color_cache[elevation] = TerrainColors.get_color(elevation, self.terrain.max_elevation)
        
        base_color = self.color_cache[elevation]
        
        # If lighting is disabled or this is an obstacle, return the base color
        if not self.use_lighting or elevation < 0 or not neighbors:
            return base_color
        
        # Calculate normal vector based on neighboring elevations
        dx = neighbors.get("right", elevation) - neighbors.get("left", elevation)
        dy = neighbors.get("bottom", elevation) - neighbors.get("top", elevation)
        
        # Normalize the vector
        length = max(0.001, math.sqrt(dx*dx + dy*dy))
        normal = (dx/length, dy/length, 1.0/length)
        
        # Calculate diffuse lighting using dot product with light direction
        light_dir = (self.light_direction[0], self.light_direction[1], -1.0)
        length = math.sqrt(light_dir[0]**2 + light_dir[1]**2 + light_dir[2]**2)
        light_dir = (light_dir[0]/length, light_dir[1]/length, light_dir[2]/length)
        
        diffuse = max(0, normal[0]*light_dir[0] + normal[1]*light_dir[1] + normal[2]*light_dir[2])
        
        # Calculate final light factor
        light_factor = self.ambient_light + (1.0 - self.ambient_light) * diffuse
        
        # Apply lighting to color
        return TerrainColors.get_shaded_color(base_color, light_factor)
    
    def render(self, camera, player_pos, path=None, destination=None):
        """
        Render the visible terrain centered on the player.
        
        Args:
            camera (Camera): Camera instance
            player_pos (tuple): Player's position (x, y)
            path (list): List of path waypoints
            destination (tuple): Destination position (x, y)
        """
        screen_width, screen_height = self.screen.get_size()
        
        # Calculate the visible area in world coordinates
        visible_area_width = screen_width / camera.zoom
        visible_area_height = screen_height / camera.zoom
        
        # Calculate the start and end positions to render
        start_x = int(camera.x - visible_area_width / 2)
        start_y = int(camera.y - visible_area_height / 2)
        end_x = int(camera.x + visible_area_width / 2)
        end_y = int(camera.y + visible_area_height / 2)
        
        # Limit to view distance
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.terrain.width, end_x)
        end_y = min(self.terrain.height, end_y)
        
        # Calculate step size based on zoom level
        step = max(1, int(1 / camera.zoom))
        
        # Precompute visible blocks and their elevations
        visible_blocks = {}
        for x in range(start_x, end_x, step):
            for y in range(start_y, end_y, step):
                elevation = self.terrain.get_elevation(x, y)
                visible_blocks[(x, y)] = elevation
        
        # Render the visible terrain
        for x in range(start_x, end_x, step):
            for y in range(start_y, end_y, step):
                # Get the elevation at this position
                elevation = visible_blocks.get((x, y), -1)
                
                # Get neighbor elevations for lighting
                if self.use_lighting and elevation >= 0:
                    neighbors = {
                        "left": visible_blocks.get((x-step, y), elevation),
                        "right": visible_blocks.get((x+step, y), elevation),
                        "top": visible_blocks.get((x, y-step), elevation),
                        "bottom": visible_blocks.get((x, y+step), elevation)
                    }
                else:
                    neighbors = None
                
                # Calculate the color based on elevation and lighting
                color = self.get_color(elevation, x, y, neighbors)
                
                # Convert world coordinates to screen coordinates
                screen_x, screen_y = camera.world_to_screen(x, y, screen_width, screen_height)
                
                # Calculate the size of the block based on zoom level
                block_size = max(1, int(self.block_size * camera.zoom))
                
                # Draw a rect at this position
                pygame.draw.rect(self.screen, color, (screen_x, screen_y, block_size, block_size))
        
        # Draw the player's position
        player_x, player_y = camera.world_to_screen(player_pos[0], player_pos[1], screen_width, screen_height)
        pygame.draw.circle(self.screen, (0, 0, 255), (int(player_x), int(player_y)), max(3, int(5 * camera.zoom)))
        
        # Draw the destination point if set
        if destination:
            dest_x, dest_y = camera.world_to_screen(destination[0], destination[1], screen_width, screen_height)
            # Draw a larger red circle for the destination
            pygame.draw.circle(self.screen, (255, 0, 0), (int(dest_x), int(dest_y)), max(4, int(6 * camera.zoom)))
            # Draw an X inside the circle for better visibility
            x_size = max(3, int(4 * camera.zoom))
            pygame.draw.line(self.screen, (255, 255, 255), 
                            (int(dest_x) - x_size, int(dest_y) - x_size),
                            (int(dest_x) + x_size, int(dest_y) + x_size), 2)
            pygame.draw.line(self.screen, (255, 255, 255), 
                            (int(dest_x) - x_size, int(dest_y) + x_size),
                            (int(dest_x) + x_size, int(dest_y) - x_size), 2)
        
        # Draw the path if available
        if path:
            points = []
            for p in path:
                x, y = camera.world_to_screen(p[0], p[1], screen_width, screen_height)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, (0, 255, 0), False, points, max(2, int(3 * camera.zoom)))

    def render_first_person(self, camera, player_pos, player_direction, player_height, path=None, destination=None):
        """
        Render the terrain from a first-person perspective.
        
        Args:
            camera (FirstPersonCamera): First-person camera instance
            player_pos (tuple): Player's position (x, y)
            player_direction (float): Player's direction in radians
            player_height (float): Player's height above the terrain
            path (list): List of path waypoints
            destination (tuple): Destination position (x, y)
        """
        screen_width, screen_height = self.screen.get_size()
        
        # Draw sky gradient
        # Create a vertical gradient from sky color to horizon color
        for y in range(screen_height // 2):
            # Calculate interpolation factor (0 at top, 1 at horizon)
            t = y / (screen_height / 2)
            r = int(self.sky_color[0] * (1 - t) + self.horizon_color[0] * t)
            g = int(self.sky_color[1] * (1 - t) + self.horizon_color[1] * t)
            b = int(self.sky_color[2] * (1 - t) + self.horizon_color[2] * t)
            
            # Draw a horizontal line of the gradient color
            pygame.draw.line(self.screen, (r, g, b), (0, y), (screen_width, y))
        
        # Draw a more detailed horizon line
        pygame.draw.line(self.screen, (100, 80, 60), (0, screen_height // 2), (screen_width, screen_height // 2), 2)
        
        # Draw ground in the bottom half of the screen with a gradient for distance
        ground_height = screen_height // 2
        for y in range(ground_height, screen_height):
            # Make ground darker with distance from horizon
            distance_factor = (y - ground_height) / (screen_height - ground_height)
            base_color = (160, 120, 80)
            darker_color = (
                int(base_color[0] * (1 - distance_factor * 0.5)),
                int(base_color[1] * (1 - distance_factor * 0.5)),
                int(base_color[2] * (1 - distance_factor * 0.5))
            )
            pygame.draw.line(self.screen, darker_color, (0, y), (screen_width, y))
        
        # Draw grid lines on ground for better depth perception
        grid_spacing = 50
        horizon_y = screen_height // 2
        vanishing_point_x = screen_width // 2
        
        # Draw vertical grid lines (running away from viewer)
        for x_offset in range(-10, 11, 2):
            start_x = vanishing_point_x + x_offset * grid_spacing
            if 0 <= start_x < screen_width:
                # Draw lines radiating from vanishing point
                for i in range(1, 6):
                    # Further lines are drawn thinner and lighter
                    line_width = max(1, 3 - i // 2)
                    intensity = max(30, 100 - i * 15)
                    grid_color = (intensity, intensity, intensity)
                    
                    # Calculate endpoints based on distance
                    distance_factor = i / 5
                    end_x = vanishing_point_x + (start_x - vanishing_point_x) * (1 + distance_factor * 5)
                    end_y = horizon_y + (screen_height - horizon_y) * distance_factor
                    
                    # Only draw if end point is on screen
                    if 0 <= end_x < screen_width:
                        pygame.draw.line(self.screen, grid_color, (start_x, horizon_y), (end_x, end_y), line_width)
        
        # Render visible terrain using improved raycasting
        ray_step = 2  # Number of pixels to skip between rays for performance
        
        # Pre-compute some constants
        max_dist = camera.view_distance
        cam_x, cam_y = camera.position
        
        # Create a list to store rendered columns for post-processing
        terrain_columns = []
        
        for x in range(0, screen_width, ray_step):
            # Calculate ray direction for this column
            ray_dir = camera.get_view_ray(x, screen_height // 2, screen_width, screen_height)
            ray_x, ray_y = ray_dir
            
            # Cast the ray to find the first terrain intersection
            step_size = 1
            dist = 0
            hit = False
            hit_pos = None
            hit_elevation = None
            
            while dist < max_dist and not hit:
                # Calculate current position along the ray
                pos_x = int(cam_x + ray_x * dist)
                pos_y = int(cam_y + ray_y * dist)
                
                # Check if position is in bounds
                if (0 <= pos_x < self.terrain.width and 0 <= pos_y < self.terrain.height):
                    # Get the elevation at this position
                    elevation = self.terrain.get_elevation(pos_x, pos_y)
                    
                    # Check if the ray hits the terrain
                    if elevation >= 0 and elevation >= camera.height - 3:  # Can see 3 blocks below current height
                        hit = True
                        hit_pos = (pos_x, pos_y)
                        hit_elevation = elevation
                
                # Increase distance for next step
                dist += step_size
                
                # Adaptive step size for performance
                step_size = max(1, int(dist / 10))
            
            if hit:
                # Store hit information for post-processing
                terrain_columns.append((x, dist, hit_pos, hit_elevation))
        
        # Sort columns by distance for correct rendering
        terrain_columns.sort(key=lambda col: col[1], reverse=True)
        
        # Post-process and render terrain columns
        for x, dist, hit_pos, elevation in terrain_columns:
            # Calculate perceived height based on elevation difference
            height_diff = elevation - camera.height
            
            # More extreme height rendering for better visibility
            screen_height_factor = -height_diff / 10 + 0.5  # 0 = horizon, 1 = bottom of screen
            
            # Map to screen coordinates
            screen_y = int(screen_height * (0.5 + screen_height_factor / 2))
            screen_y = max(screen_height // 2, min(screen_height, screen_y))
            
            # Calculate the block width based on distance
            block_width = max(ray_step, int(ray_step * (1 + (max_dist - dist) / max_dist * 2)))
            
            # Get base color for this elevation
            base_color = TerrainColors.get_color(elevation, self.terrain.max_elevation)
            
            # Apply distance fog
            fog_factor = 1.0 - min(0.8, dist / max_dist)
            shaded_color = (
                int(base_color[0] * fog_factor),
                int(base_color[1] * fog_factor),
                int(base_color[2] * fog_factor)
            )
            
            # Apply terrain height shading for better 3D appearance
            if height_diff > 0:
                # Higher terrain is lighter
                brightness = min(1.2, 1.0 + height_diff / 50)
                shaded_color = (
                    min(255, int(shaded_color[0] * brightness)),
                    min(255, int(shaded_color[1] * brightness)),
                    min(255, int(shaded_color[2] * brightness))
                )
            elif height_diff < 0:
                # Lower terrain is darker
                darkness = max(0.7, 1.0 + height_diff / 30)
                shaded_color = (
                    max(0, int(shaded_color[0] * darkness)),
                    max(0, int(shaded_color[1] * darkness)),
                    max(0, int(shaded_color[2] * darkness))
                )
            
            # Draw a vertical column for this terrain slice
            # Use a rectangle instead of a line for more continuous appearance
            terrain_rect = pygame.Rect(x, screen_y, block_width, screen_height - screen_y)
            pygame.draw.rect(self.screen, shaded_color, terrain_rect)
            
            # Add a subtle highlight at the top edge of the terrain
            pygame.draw.line(self.screen, (
                min(255, int(shaded_color[0] * 1.2)),
                min(255, int(shaded_color[1] * 1.2)),
                min(255, int(shaded_color[2] * 1.2))
            ), (x, screen_y), (x + block_width, screen_y), 2)
            
            # Check if this is the destination point and draw a marker
            if destination and hit_pos:
                pos_x, pos_y = hit_pos
                if abs(pos_x - destination[0]) < 3 and abs(pos_y - destination[1]) < 3:
                    # Draw a more visible red marker for the destination
                    marker_size = max(5, int(15 * (1 - dist / max_dist)))
                    marker_x = x + block_width // 2
                    pygame.draw.circle(self.screen, (255, 0, 0), (marker_x, screen_y), marker_size)
                    # Add an X inside the circle
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                    (marker_x - marker_size/2, screen_y - marker_size/2),
                                    (marker_x + marker_size/2, screen_y + marker_size/2), 2)
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                    (marker_x - marker_size/2, screen_y + marker_size/2),
                                    (marker_x + marker_size/2, screen_y - marker_size/2), 2)
            
            # Check if this is on the path
            if path and hit_pos:
                pos_x, pos_y = hit_pos
                for path_pos in path:
                    if abs(pos_x - path_pos[0]) < 3 and abs(pos_y - path_pos[1]) < 3:
                        # Draw a more visible green marker for path points
                        marker_size = max(3, int(8 * (1 - dist / max_dist)))
                        marker_x = x + block_width // 2
                        pygame.draw.circle(self.screen, (0, 255, 0), (marker_x, screen_y), marker_size)
                        break
        
        # Draw a clearer crosshair in the center of the screen
        crosshair_size = 12
        crosshair_thickness = 2
        crosshair_color = (255, 255, 255)
        crosshair_center = (screen_width // 2, screen_height // 2)
        
        # Outer circle
        pygame.draw.circle(self.screen, crosshair_color, crosshair_center, crosshair_size, 1)
        
        # Inner dot
        pygame.draw.circle(self.screen, crosshair_color, crosshair_center, 2)
        
        # Crosshair lines
        pygame.draw.line(self.screen, crosshair_color, 
                        (crosshair_center[0] - crosshair_size, crosshair_center[1]),
                        (crosshair_center[0] - 4, crosshair_center[1]), crosshair_thickness)
        pygame.draw.line(self.screen, crosshair_color, 
                        (crosshair_center[0] + 4, crosshair_center[1]),
                        (crosshair_center[0] + crosshair_size, crosshair_center[1]), crosshair_thickness)
        pygame.draw.line(self.screen, crosshair_color, 
                        (crosshair_center[0], crosshair_center[1] - crosshair_size),
                        (crosshair_center[0], crosshair_center[1] - 4), crosshair_thickness)
        pygame.draw.line(self.screen, crosshair_color, 
                        (crosshair_center[0], crosshair_center[1] + 4),
                        (crosshair_center[0], crosshair_center[1] + crosshair_size), crosshair_thickness)
        
        # Draw elevation indicator on the left side
        elevation_indicator_width = 20
        elevation_indicator_height = 150
        elevation_x = 20
        elevation_y = (screen_height - elevation_indicator_height) // 2
        
        # Draw background
        pygame.draw.rect(self.screen, (30, 30, 30), 
                        (elevation_x, elevation_y, elevation_indicator_width, elevation_indicator_height))
        
        # Draw current elevation indicator
        if self.terrain.max_elevation > 0:
            normalized_elevation = min(1.0, max(0.0, player_height / self.terrain.max_elevation))
            indicator_height = int(elevation_indicator_height * normalized_elevation)
            indicator_y = elevation_y + elevation_indicator_height - indicator_height
            
            # Draw filled bar
            pygame.draw.rect(self.screen, (0, 200, 0), 
                            (elevation_x, indicator_y, elevation_indicator_width, indicator_height))
            
            # Draw marker for current position
            pygame.draw.rect(self.screen, (255, 255, 255), 
                            (elevation_x, indicator_y, elevation_indicator_width, 3))
        
        # Label the elevation bar
        elevation_label = "Elevation"
        font = pygame.font.SysFont("Arial", 18)
        label_surface = font.render(elevation_label, True, (255, 255, 255))
        self.screen.blit(label_surface, 
                        (elevation_x + elevation_indicator_width // 2 - label_surface.get_width() // 2, 
                        elevation_y + elevation_indicator_height + 5))


class GUI:
    def __init__(self, width=1024, height=768, fullscreen=False):
        """
        Initialize the GUI.
        
        Args:
            width (int): Screen width
            height (int): Screen height
            fullscreen (bool): Whether to use fullscreen mode
        """
        pygame.init()
        
        # Set up the display
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.width, self.height = self.screen.get_size()
        else:
            self.width = width
            self.height = height
            self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption("Mars Terrain Simulator")
        
        # Set up the clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Font for rendering text
        self.font = pygame.font.SysFont("Arial", 18)
        
        # Status messages
        self.status_messages = []
        self.message_timeout = 3000  # Message timeout in milliseconds
        self.message_times = []
        
        # First-person mode
        self.first_person_mode = False
    
    def clear_screen(self):
        """Clear the screen with a black background."""
        self.screen.fill((0, 0, 0))
    
    def render_text(self, text, position, color=(255, 255, 255)):
        """
        Render text on the screen.
        
        Args:
            text (str): Text to render
            position (tuple): Position (x, y)
            color (tuple): RGB color values (r, g, b)
        """
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)
    
    def add_status_message(self, message, color=(255, 255, 255)):
        """
        Add a status message to be displayed temporarily.
        
        Args:
            message (str): Message to display
            color (tuple): RGB color values (r, g, b)
        """
        self.status_messages.append((message, color))
        self.message_times.append(pygame.time.get_ticks())
    
    def update_status_messages(self):
        """Update and remove expired status messages."""
        current_time = pygame.time.get_ticks()
        
        # Check for expired messages
        i = 0
        while i < len(self.status_messages):
            if current_time - self.message_times[i] > self.message_timeout:
                self.status_messages.pop(i)
                self.message_times.pop(i)
            else:
                i += 1
    
    def render_status_messages(self):
        """Render all active status messages."""
        y = 50
        for i, (message, color) in enumerate(self.status_messages):
            self.render_text(message, (10, y), color)
            y += 25
    
    def render_hud(self, player_pos, elevation, autopilot_enabled, first_person_mode=False):
        """
        Render the heads-up display.
        
        Args:
            player_pos (tuple): Player's position (x, y)
            elevation (float): Current elevation
            autopilot_enabled (bool): Whether autopilot is enabled
            first_person_mode (bool): Whether first-person mode is enabled
        """
        # Render player position
        pos_text = f"Position: ({player_pos[0]:.1f}, {player_pos[1]:.1f})"
        self.render_text(pos_text, (10, 10))
        
        # Render elevation
        elev_text = f"Elevation: {elevation:.1f}"
        self.render_text(elev_text, (10, 30))
        
        # Render autopilot status
        if autopilot_enabled:
            self.render_text("Autopilot: ENABLED", (self.width - 200, 10), (0, 255, 0))
        else:
            self.render_text("Autopilot: DISABLED", (self.width - 200, 10), (255, 0, 0))
        
        # Render view mode
        if first_person_mode:
            self.render_text("View: FIRST-PERSON", (self.width - 200, 30), (0, 255, 255))
        else:
            self.render_text("View: TOP-DOWN", (self.width - 200, 30), (255, 255, 0))
        
        # Render controls help appropriate for the current view mode
        if first_person_mode:
            controls_text = "Controls: WASD=Move, Mouse=Look, K=Toggle Autopilot, R=Toggle View"
        else:
            controls_text = "Controls: WASD=Move, K=Toggle Autopilot, R=Toggle View, Scroll=Zoom"
        
        self.render_text(controls_text, (10, self.height - 50))
        
        # Render destination help
        if not first_person_mode:
            click_text = "Click anywhere on the terrain to set a destination point"
            self.render_text(click_text, (10, self.height - 30), (255, 255, 0))
        else:
            jump_text = "In first-person mode, the rover can climb up to 2 blocks"
            self.render_text(jump_text, (10, self.height - 30), (255, 255, 0))
    
    def update(self):
        """Update the display."""
        pygame.display.flip()
        self.clock.tick(self.fps)
    
    def quit(self):
        """Quit pygame and exit."""
        pygame.quit() 