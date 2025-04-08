import pygame
import time
import math

class PlayerController:
    def __init__(self, terrain, pathfinder, gui, initial_pos=(0, 0)):
        """
        Initialize the player controller.
        
        Args:
            terrain (TerrainGenerator): Terrain generator instance
            pathfinder (PathFinder): Pathfinder instance
            gui (GUI): GUI instance for displaying messages
            initial_pos (tuple): Initial player position (x, y)
        """
        self.terrain = terrain
        self.pathfinder = pathfinder
        self.gui = gui
        self.position = initial_pos
        
        # Movement parameters
        self.speed = 10.0  # Base movement speed
        self.diagonal_factor = 0.7071  # 1/sqrt(2) for diagonal movement
        
        # Autopilot parameters
        self.autopilot_enabled = False
        self.destination = None
        self.path = None
        self.current_path_index = 0
        self.path_recalculation_interval = 5.0  # seconds
        self.last_path_calculation = 0
        
    def get_position(self):
        """Get the current player position."""
        return self.position
    
    def get_elevation(self):
        """Get the elevation at the current player position."""
        x, y = int(self.position[0]), int(self.position[1])
        return self.terrain.get_elevation(x, y)
    
    def move(self, dx, dy):
        """
        Move the player by the specified amount.
        
        Args:
            dx (float): Movement in x direction
            dy (float): Movement in y direction
            
        Returns:
            bool: Whether the move was successful
        """
        # Calculate new position
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        
        # Check if the new position is within bounds and not an obstacle
        if (0 <= new_x < self.terrain.width and 
            0 <= new_y < self.terrain.height and 
            not self.terrain.is_obstacle(int(new_x), int(new_y))):
            
            # Check elevation difference
            current_elev = self.terrain.get_elevation(int(self.position[0]), int(self.position[1]))
            new_elev = self.terrain.get_elevation(int(new_x), int(new_y))
            
            if current_elev == -1 or new_elev == -1:
                return False  # Cannot move to/from obstacles
            
            # Limit movement based on elevation difference
            elev_diff = abs(current_elev - new_elev)
            if elev_diff > self.terrain.max_elevation / 10:
                # Movement is possible but very slow when climbing steep slopes
                dx *= 0.1
                dy *= 0.1
                new_x = self.position[0] + dx
                new_y = self.position[1] + dy
            
            # Update position
            self.position = (new_x, new_y)
            return True
        
        return False
    
    def handle_input(self, keys):
        """
        Handle user input for movement.
        
        Args:
            keys (pygame.key.get_pressed()): Pressed keys
            
        Returns:
            bool: Whether the player moved
        """
        if self.autopilot_enabled:
            return False  # Don't process manual movement when autopilot is enabled
        
        dx, dy = 0, 0
        
        # Handle WASD keys for movement
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= self.diagonal_factor
            dy *= self.diagonal_factor
        
        # Apply movement speed
        dx *= self.speed
        dy *= self.speed
        
        # Attempt to move
        if dx != 0 or dy != 0:
            return self.move(dx, dy)
        
        return False
    
    def set_destination(self, destination):
        """
        Set the destination for autopilot.
        
        Args:
            destination (tuple): Destination position (x, y)
            
        Returns:
            bool: Whether the destination was set successfully
        """
        if destination is None:
            return False
        
        self.destination = destination
        
        # Calculate initial path prioritizing minimal elevation changes
        self.calculate_path(optimize_for_elevation=True)
        
        return True
    
    def calculate_path(self, optimize_for_elevation=True):
        """
        Calculate the path to the current destination.
        
        Args:
            optimize_for_elevation (bool): Whether to optimize for minimal elevation changes
        """
        if self.destination is None:
            self.path = None
            return
        
        # Use A* to find the path
        start = (int(self.position[0]), int(self.position[1]))
        goal = (int(self.destination[0]), int(self.destination[1]))
        
        # Use the PathFinder's A* algorithm with enhanced elevation-based costs
        if optimize_for_elevation:
            # Set a higher weight on elevation differences in the pathfinder temporarily
            original_elevation_weight = self.pathfinder.elevation_weight
            self.pathfinder.elevation_weight = 3.0  # Increase weight for elevation changes
            self.path = self.pathfinder.a_star(start, goal)
            self.pathfinder.elevation_weight = original_elevation_weight  # Restore original weight
        else:
            self.path = self.pathfinder.a_star(start, goal)
            
        self.current_path_index = 0
        self.last_path_calculation = time.time()
        
        if self.path is None:
            print("No path found to destination")
            self.gui.add_status_message("No valid path found!", (255, 0, 0))
        else:
            # Display the estimated path cost based on elevation changes
            total_elevation_changes = 0
            for i in range(len(self.path) - 1):
                current = self.path[i]
                next_point = self.path[i + 1]
                current_elev = self.terrain.get_elevation(current[0], current[1])
                next_elev = self.terrain.get_elevation(next_point[0], next_point[1])
                total_elevation_changes += abs(current_elev - next_elev)
            
            self.gui.add_status_message(f"Path found! Total elevation changes: {total_elevation_changes:.1f}", (0, 255, 0))
    
    def toggle_autopilot(self):
        """Toggle autopilot mode."""
        if self.destination is None:
            self.autopilot_enabled = False
            return False
        
        self.autopilot_enabled = not self.autopilot_enabled
        
        if self.autopilot_enabled:
            # Recalculate path when enabling autopilot
            self.calculate_path()
        
        return self.autopilot_enabled
    
    def update_autopilot(self):
        """
        Update autopilot navigation.
        
        Returns:
            bool: Whether the player moved
        """
        if not self.autopilot_enabled or self.path is None:
            return False
        
        # Check if we've reached the destination
        if self.current_path_index >= len(self.path) - 1:
            self.autopilot_enabled = False
            return False
        
        # Check if we need to recalculate the path
        current_time = time.time()
        if current_time - self.last_path_calculation > self.path_recalculation_interval:
            self.calculate_path()
        
        # Get the next waypoint
        next_waypoint = self.path[self.current_path_index + 1]
        
        # Calculate direction to the waypoint
        dx = next_waypoint[0] - self.position[0]
        dy = next_waypoint[1] - self.position[1]
        
        # Check if we've reached the waypoint
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < 1.0:
            self.current_path_index += 1
            return True
        
        # Normalize the direction
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Apply movement speed
        dx *= self.speed * 0.5  # Move slower in autopilot mode for safety
        dy *= self.speed * 0.5
        
        # Move towards the waypoint
        return self.move(dx, dy)


class InputHandler:
    def __init__(self, gui, controller, camera, minimap):
        """
        Initialize the input handler.
        
        Args:
            gui (GUI): GUI instance
            controller (PlayerController): Player controller instance
            camera (Camera): Camera instance
            minimap (Minimap): Minimap instance
        """
        self.gui = gui
        self.controller = controller
        self.camera = camera
        self.minimap = minimap
        
        # Mouse state
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        self.drag_start_time = 0
        self.is_dragging = False
        
        # Key handling
        self.keys_pressed = {}
        self.key_cooldown = {}
        self.key_cooldown_time = 0.2  # seconds
    
    def handle_events(self):
        """
        Handle pygame events.
        
        Returns:
            bool: Whether the application should quit
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            
            elif event.type == pygame.KEYDOWN:
                # Handle key presses
                if event.key == pygame.K_ESCAPE:
                    return True
                
                # Toggle autopilot with K key
                if event.key == pygame.K_k:
                    current_time = time.time()
                    if current_time - self.key_cooldown.get(pygame.K_k, 0) > self.key_cooldown_time:
                        self.key_cooldown[pygame.K_k] = current_time
                        autopilot_enabled = self.controller.toggle_autopilot()
                        if autopilot_enabled:
                            self.gui.add_status_message("Autopilot ENABLED", (0, 255, 0))
                        else:
                            self.gui.add_status_message("Autopilot DISABLED", (255, 0, 0))
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks
                if event.button == 1:  # Left click
                    self.mouse_down = True
                    self.last_mouse_pos = event.pos
                    self.drag_start_time = time.time()
                    self.is_dragging = False
                    
                    # Check if click is on minimap to set destination
                    destination = self.minimap.set_destination(event.pos[0], event.pos[1])
                    if destination:
                        self.controller.set_destination(destination)
                        self.gui.add_status_message(f"Destination set: {destination}", (255, 255, 0))
                
                # Handle mouse wheel for zoom
                elif event.button == 4:  # Scroll up
                    self.camera.zoom_in()
                elif event.button == 5:  # Scroll down
                    self.camera.zoom_out()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    # If this was a short click (not a drag) and not on minimap, set destination on main view
                    if not self.is_dragging and time.time() - self.drag_start_time < 0.2:
                        # First check if we're NOT clicking on the minimap area
                        if not (self.minimap.x_offset <= event.pos[0] <= self.minimap.x_offset + self.minimap.width and
                                self.minimap.y_offset <= event.pos[1] <= self.minimap.y_offset + self.minimap.height):
                            # Convert screen coordinates to world coordinates
                            screen_width, screen_height = self.gui.screen.get_size()
                            world_x, world_y = self.camera.screen_to_world(event.pos[0], event.pos[1], 
                                                                          screen_width, screen_height)
                            
                            # Set destination if valid (non-obstacle)
                            if (0 <= world_x < self.controller.terrain.width and 
                                0 <= world_y < self.controller.terrain.height and
                                not self.controller.terrain.is_obstacle(int(world_x), int(world_y))):
                                
                                destination = (int(world_x), int(world_y))
                                self.controller.set_destination(destination)
                                # Also update minimap
                                self.minimap.destination = destination
                                self.gui.add_status_message(f"Destination set: {destination}", (255, 255, 0))
                    
                    self.mouse_down = False
                    self.is_dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle mouse drag for camera movement
                if self.mouse_down:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    
                    # If the mouse has moved more than a threshold, mark as dragging
                    if abs(dx) > 5 or abs(dy) > 5:
                        self.is_dragging = True
                    
                    # Move camera in the opposite direction of mouse movement
                    self.camera.move(-dx / self.camera.zoom, -dy / self.camera.zoom)
                    
                    self.last_mouse_pos = event.pos
        
        return False
    
    def update(self):
        """
        Update input handling.
        
        Returns:
            bool: Whether the application should quit
        """
        # Handle events
        if self.handle_events():
            return True
        
        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        player_moved = self.controller.handle_input(keys)
        
        # Update autopilot
        autopilot_moved = self.controller.update_autopilot()
        
        # If player moved, update camera to follow player
        if player_moved or autopilot_moved:
            player_pos = self.controller.get_position()
            self.camera.set_position(player_pos[0], player_pos[1])
        
        return False 