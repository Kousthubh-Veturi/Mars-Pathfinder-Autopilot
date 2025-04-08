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
        
        # First-person movement parameters
        self.first_person_mode = False
        self.direction = 0.0  # Direction in radians (0 = positive x-axis)
        self.max_climb_height = 2.0  # Maximum height the rover can climb/jump in blocks
        self.first_person_speed = 5.0  # Movement speed in first-person mode (blocks per second)
        
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
        
        # Check if the new position is within bounds
        if not (0 <= new_x < self.terrain.width and 0 <= new_y < self.terrain.height):
            return False
        
        # Get current and new elevations
        current_elev = self.terrain.get_elevation(int(self.position[0]), int(self.position[1]))
        new_elev = self.terrain.get_elevation(int(new_x), int(new_y))
        
        # Check if the new position is an obstacle
        if new_elev < 0:
            return False  # Cannot move to obstacles
        
        # Check if current position is an obstacle (shouldn't happen, but just in case)
        if current_elev < 0:
            current_elev = 0  # Assume zero elevation if in an obstacle
        
        # Calculate elevation difference
        elev_diff = new_elev - current_elev
        
        # In first-person mode, allow climbing/jumping up to max_climb_height
        if self.first_person_mode:
            # If trying to climb too high, prevent movement
            if elev_diff > self.max_climb_height:
                return False
        else:
            # In top-down mode, slow down movement on steep slopes
            if elev_diff > self.terrain.max_elevation / 10:
                # Movement is possible but very slow when climbing steep slopes
                dx *= 0.1
                dy *= 0.1
                new_x = self.position[0] + dx
                new_y = self.position[1] + dy
        
        # Update position
        self.position = (new_x, new_y)
        
        # Update player direction based on movement (only in first-person mode)
        if self.first_person_mode and (dx != 0 or dy != 0):
            # Only update direction if actually moving
            self.direction = math.atan2(dy, dx)
        
        return True
    
    def toggle_first_person_mode(self):
        """Toggle between first-person and top-down modes."""
        self.first_person_mode = not self.first_person_mode
        return self.first_person_mode
    
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
        
        if self.first_person_mode:
            # First-person movement is relative to the camera direction
            forward = False
            backward = False
            left = False
            right = False
            
            # Handle WASD keys
            if keys[pygame.K_w]:
                forward = True
            if keys[pygame.K_s]:
                backward = True
            if keys[pygame.K_a]:
                left = True
            if keys[pygame.K_d]:
                right = True
            
            # Calculate movement vector based on direction
            if forward:
                dx += math.cos(self.direction) * self.first_person_speed
                dy += math.sin(self.direction) * self.first_person_speed
            if backward:
                dx -= math.cos(self.direction) * self.first_person_speed * 0.5  # Move backward more slowly
                dy -= math.sin(self.direction) * self.first_person_speed * 0.5
            if left:
                # Strafe left (90 degrees to the left of forward direction)
                dx += math.cos(self.direction - math.pi/2) * self.first_person_speed * 0.7
                dy += math.sin(self.direction - math.pi/2) * self.first_person_speed * 0.7
            if right:
                # Strafe right (90 degrees to the right of forward direction)
                dx += math.cos(self.direction + math.pi/2) * self.first_person_speed * 0.7
                dy += math.sin(self.direction + math.pi/2) * self.first_person_speed * 0.7
            
            # Normalize diagonal movement
            if (forward or backward) and (left or right):
                dx *= self.diagonal_factor
                dy *= self.diagonal_factor
            
            # Apply frame-rate independent movement (assuming 60 FPS)
            dx /= 60
            dy /= 60
            
        else:
            # Top-down movement is grid-aligned
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
            dx *= self.speed / 60  # Make speed frame-rate independent
            dy *= self.speed / 60
        
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
        
        # Update direction based on movement in first-person mode
        if self.first_person_mode:
            self.direction = math.atan2(dy, dx)
        
        # Check if we've reached the waypoint
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < 1.0:
            self.current_path_index += 1
            return True
        
        # Normalize the direction
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Apply movement speed (use first-person speed if in that mode)
        if self.first_person_mode:
            speed = self.first_person_speed * 0.5 / 60
        else:
            speed = self.speed * 0.5 / 60
        
        dx *= speed  # Move slower in autopilot mode for safety
        dy *= speed
        
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
        
        # First-person camera
        self.first_person_camera = None
        
        # Mouse state
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        self.drag_start_time = 0
        self.is_dragging = False
        
        # Mouse lock for first-person mode
        self.mouse_locked = False
        self.mouse_sensitivity = 0.5
        
        # Key handling
        self.keys_pressed = {}
        self.key_cooldown = {}
        self.key_cooldown_time = 0.2  # seconds
    
    def set_first_person_camera(self, fp_camera):
        """Set the first-person camera instance."""
        self.first_person_camera = fp_camera
    
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
                    # If in first-person mode with locked mouse, unlock the mouse
                    if self.gui.first_person_mode and self.mouse_locked:
                        self.mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        return True  # Otherwise, exit the application
                
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
                
                # Toggle first-person mode with R key
                if event.key == pygame.K_r:
                    current_time = time.time()
                    if current_time - self.key_cooldown.get(pygame.K_r, 0) > self.key_cooldown_time:
                        self.key_cooldown[pygame.K_r] = current_time
                        
                        # Toggle first-person mode in controller
                        first_person_mode = self.controller.toggle_first_person_mode()
                        
                        # Update GUI flag
                        self.gui.first_person_mode = first_person_mode
                        
                        if first_person_mode:
                            self.gui.add_status_message("First-person mode ENABLED", (0, 255, 255))
                            # Initialize first-person camera position and direction
                            self.first_person_camera.set_position(
                                self.controller.position[0], 
                                self.controller.position[1],
                                self.controller.terrain
                            )
                            self.first_person_camera.set_direction(self.controller.direction)
                            
                            # Reset mouse lock state
                            self.mouse_locked = False
                        else:
                            self.gui.add_status_message("First-person mode DISABLED", (255, 255, 0))
                            # Make sure mouse is visible and not grabbed
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                            self.mouse_locked = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks
                if event.button == 1:  # Left click
                    if self.gui.first_person_mode:
                        # In first-person mode, left click toggles mouse lock for camera control
                        if not self.mouse_locked:
                            self.mouse_locked = True
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                            # Center mouse position
                            screen_width, screen_height = self.gui.screen.get_size()
                            pygame.mouse.set_pos(screen_width // 2, screen_height // 2)
                        else:
                            self.mouse_locked = False
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                    else:
                        # Normal top-down mode
                        self.mouse_down = True
                        self.last_mouse_pos = event.pos
                        self.drag_start_time = time.time()
                        self.is_dragging = False
                        
                        # Check if click is on minimap to set destination
                        destination = self.minimap.set_destination(event.pos[0], event.pos[1])
                        if destination:
                            self.controller.set_destination(destination)
                            self.gui.add_status_message(f"Destination set: {destination}", (255, 255, 0))
                
                # Handle mouse wheel for zoom (only in top-down mode)
                if not self.gui.first_person_mode:
                    if event.button == 4:  # Scroll up
                        self.camera.zoom_in()
                    elif event.button == 5:  # Scroll down
                        self.camera.zoom_out()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    if not self.gui.first_person_mode:
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
                if self.gui.first_person_mode and self.mouse_locked:
                    # Handle mouse movement for first-person camera rotation
                    screen_width, screen_height = self.gui.screen.get_size()
                    center_x, center_y = screen_width // 2, screen_height // 2
                    
                    # Calculate mouse movement from center
                    dx = event.pos[0] - center_x
                    dy = event.pos[1] - center_y
                    
                    if dx != 0 or dy != 0:
                        # Rotate the camera based on mouse movement
                        self.first_person_camera.rotate(dx * self.mouse_sensitivity, dy * self.mouse_sensitivity)
                        
                        # Reset mouse position to center
                        pygame.mouse.set_pos(center_x, center_y)
                        
                        # Update controller direction to match camera
                        self.controller.direction = self.first_person_camera.direction
                
                elif self.gui.first_person_mode:
                    # In first-person mode but mouse not locked - do nothing
                    pass
                
                elif self.mouse_down:
                    # In top-down mode, handle dragging for camera movement
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
            
            if self.gui.first_person_mode:
                # In first-person mode, update first-person camera
                self.first_person_camera.set_position(
                    player_pos[0], 
                    player_pos[1],
                    self.controller.terrain
                )
            else:
                # In top-down mode, update the overhead camera
                self.camera.set_position(player_pos[0], player_pos[1])
        
        # Update first-person camera (for smooth movement)
        if self.gui.first_person_mode and self.first_person_camera:
            self.first_person_camera.update()
        
        return False 