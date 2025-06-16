import math

def parse_observation(obs):
    """Parse the game observation into a structured summary.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        dict: A structured summary containing:
            - players_positions: Dictionary of player positions and states
            - ball_position: Current position of the ball
            - ball_movement: Movement state of the ball
            - ball_owner: Current owner of the ball
            - ball_owned_team: Team in possession
            - game_mode: Current game mode
            - score: Current score
            - time: Current game time
            - Various team states (cards, designated players)
    """
    summary = {}
    # summary["players_positions"] = get_players_positions(obs)
    _, summary["ball movement"] = parse_ball_info(obs)
    # summary["ball owner"] = parse_ball_owner(obs)
    # summary["ball_owned_team"] = parse_ball_owned_team(obs)
    # summary["left_team_yellow_cards"] = get_players_with_yellow_card(obs, team="left")
    # summary["right_team_yellow_cards"] = get_players_with_yellow_card(obs, team="right")
    # summary["left_team_designated_player"] = get_designated_player(obs, team="left")
    # summary["right_team_designated_player"] = get_designated_player(obs, team="right")
    # summary["left_team_red_cards"] = get_players_with_red_card(obs, team="left")
    # summary["right_team_red_cards"] = get_players_with_red_card(obs, team="right")
    # summary["game_mode"] = parse_game_mode(obs)
    # summary["score"] = parse_score(obs)
    # summary["time"] = parse_time(obs)

    # minimap
    # ball_pos = obs.get('ball', [None, None])[0:2]
    # print_field(generate_minimap(obs["left_team"], obs["right_team"], ball_pos))
    return summary


def parse_ball_info(obs):
    """Parse ball position and movement information.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        tuple: (ball_position, ball_movement)
            - ball_position: String describing ball's position on field
            - ball_movement: String describing ball's movement state
    """
    ball = obs.get('ball', [None, None, None])
    x, y, z = ball[0:3]  # Get x, y, z coordinates
    ball_position = describe_ball_position(x, y) if x is not None and y is not None else "Unknown"
    
    # Add height information
    if z is not None:
        if z < 0.8:  # Very small z value indicates ball is on the ground
            height_info = "on the ground"
        elif z < 1.5:
            height_info = "mid-height"
        else:
            height_info = "high in the air"
        ball_position = f"{ball_position} ({height_info})"
    
    ball_movement = parse_ball_movement(obs)
    return ball_position, ball_movement

def parse_ball_owner(obs):
    """Parse information about which player/team owns the ball.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: Description of the ball owner (e.g., "Left team's Goalkeeper (Player 0)")
    """
    ball_owned_team = obs.get("ball_owned_team", -1)
    ball_owned_player = obs.get("ball_owned_player", -1)
    if ball_owned_team == -1:
        return "No one owns the ball"
    else:
        team = "Left" if ball_owned_team == 0 else "Right"
        player_id = ball_owned_player
        roles_key = f"{team.lower()}_team_roles"
        if roles_key in obs and player_id >= 0 and player_id < len(obs[roles_key]):
            role = role_to_string(obs[roles_key][player_id])
        else:
            role = f"Player {player_id}"
        return f"{team} team's {role} (Player {player_id})"


def parse_game_mode(obs):
    """Get the current game mode.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: Current game mode (e.g., "Normal", "Kick Off", etc.)
    """
    if 'game_mode' in obs:
        return game_mode_name(obs["game_mode"])
    else:
        return "Unknown"

def parse_score(obs):
    """Get the current game score.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: Current score in format "X - Y"
    """
    if 'score' in obs and len(obs['score']) == 2:
        return f"{obs['score'][0]} - {obs['score'][1]}"
    else:
        return "Unknown"

def parse_time(obs):
    """Convert game steps to match time.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: Current match time in format "MM:SS"
    """
    steps_left = obs.get('steps_left', None)
    if steps_left is None or steps_left == 'Unknown':
        return 'Unknown'
    # Map steps_left (3000 to 0) to time (0:00 to 90:00)
    total_steps = 3000
    total_seconds = 90 * 60
    seconds_elapsed = int((total_steps - steps_left) * total_seconds / total_steps)
    minutes = seconds_elapsed // 60
    seconds = seconds_elapsed % 60
    return f"{minutes:02d}:{seconds:02d}"

def describe_ball_position(x, y):
    """Convert x,y coordinates to field position description.
    
    Args:
        x (float): X coordinate (-1 to 1)
        y (float): Y coordinate (-1 to 1)
        
    Returns:
        str: Description of position (e.g., "left third, central area")
    """
    # X-axis zones
    if x < -0.66:
        horizontal = "left third"
    elif x < -0.1:
        horizontal = "left midfield"
    elif x < 0.1:
        horizontal = "center midfield"
    elif x < 0.66:
        horizontal = "right midfield"
    else:
        horizontal = "right third"

    # Y-axis zones
    if y < -0.20:
        vertical = "top"
    elif y > 0.20:
        vertical = "bottom"
    else:
        vertical = "central"

    return f"{horizontal}, {vertical} area"

def role_to_string(role_id):
    """Convert role ID to role name.
    
    Args:
        role_id (int): Role identifier
        
    Returns:
        str: Role name (e.g., "Goalkeeper", "Centre Back")
    """
    roles = [
        "Goalkeeper", 
        "Centre Back", 
        "Left Back", 
        "Right Back", 
        "Defensive Midfielder", 
        "Central Midfielder", 
        "Left Midfielder", 
        "Right Midfielder", 
        "Attacking Midfielder", 
        "Centre Forward"
    ]
    return roles[role_id] if 0 <= role_id < len(roles) else f"Unknown Role {role_id}"

def sticky_action_name(index):
    actions = [
        "move left", "move top-left", "move top", "move top-right",
        "move right", "move bottom-right", "move bottom", "move bottom-left",
        "sprint", "dribble"
    ]
    return actions[index] if 0 <= index < len(actions) else f"Unknown Action {index}"

def game_mode_name(mode_id):
    """Convert game mode ID to mode name.
    
    Args:
        mode_id (int): Game mode identifier
        
    Returns:
        str: Game mode name (e.g., "Normal", "Kick Off")
    """
    modes = [
        "Normal", "Kick Off", "Goal Kick", "Free Kick",
        "Corner", "Throw In", "Penalty"
    ]
    return modes[mode_id] if 0 <= mode_id < len(modes) else f"Unknown Mode {mode_id}"

def parse_ball_owned_team(obs):
    """Get which team owns the ball.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: "Left", "Right", or "None"
    """
    ball_owned_team = obs.get("ball_owned_team", -1)
    if ball_owned_team == 0:
        return "Left"
    elif ball_owned_team == 1:
        return "Right"
    else:
        return "None"

def get_players_with_yellow_card(obs, team="left"):
    """Get list of players with yellow cards.
    
    Args:
        obs (dict): The raw observation from the game environment.
        team (str): "left" or "right"
        
    Returns:
        list: List of player indices with yellow cards
    """
    key = f"{team}_team_yellow_card"
    if key in obs:
        return [i for i, has_card in enumerate(obs[key]) if has_card]
    return []

def get_players_with_red_card(obs, team="left"):
    """Get list of players with red cards.
    
    Args:
        obs (dict): The raw observation from the game environment.
        team (str): "left" or "right"
        
    Returns:
        list: List of player indices with red cards
    """
    # Placeholder: If red card info is added to obs, update this function
    return []

def get_designated_player(obs, team="left"):
    """Get the designated player for a team.
    
    Args:
        obs (dict): The raw observation from the game environment.
        team (str): "left" or "right"
        
    Returns:
        int: Index of designated player or None
    """
    key = f"{team}_team_designated_player"
    if key in obs:
        return obs[key]
    return None


def map_to_grid(pos, field_length=60, field_width=10):
    """Map x in [-1,1], y in [-1,1] to grid coordinates"""
    x, y = pos
    
    # For x (columns), map from [-1,1] to [0,cols-1]
    col = int((x + 1) / 2 * (field_length - 1))
    col = max(0, min(field_length - 1, col))
    
    # For y (rows), map from [-1,1] to [0,rows-1]
    # Scale y by 3.5 to spread out vertical positions more
    y_scaled = y * 3.5  # This will make the y range effectively [-3.5,3.5]
    # Clamp y_scaled to [-1,1] range
    y_scaled = max(-1, min(1, y_scaled))
    # Center the y-coordinate and invert it
    # First center around 0, then scale to [0,1], then map to rows
    row = int(((y_scaled + 1) / 2) * (field_width - 1))
    row = max(0, min(field_width - 1, row+1))
    
    return row, col

# Create empty field
def create_field(width, length):
    return [[' ' for _ in range(length)] for _ in range(width)]

# Place players on field
def place_players(field, positions, symbol):
    for x, y in positions:
        if 0 <= y < len(field) and 0 <= x < len(field[0]):
            field[y][x] = symbol

def add_field_markings(field, field_length=60, field_width=10):
    # Left goal
    for r in range(field_width//2 - 3, field_width//2 + 4):
        if 0 <= r < field_width:
            if field[r][0] == ' ':
                field[r][0] = '|'
    
    # Right goal  
    for r in range(field_width//2 - 3, field_width//2 + 4):
        if 0 <= r < field_width:
            if field[r][field_length-1] == ' ':
                field[r][field_length-1] = '|'
    
    # Center line
    center_col = field_length // 2
    for r in range(field_width):
        if field[r][center_col] == ' ':
            field[r][center_col] = '|'
    
    # Center circle
    center_r = field_width // 2
    for c in range(center_col - 3, center_col + 4):
        if 0 <= c < field_length and field[center_r][c] == ' ':
            field[center_r][c] = '-'

# Print field to console
def print_field(field, field_length=60):
    print("Field Layout:")
    print("L = Left Team, R = Right Team, * = Overlap, | = Field Lines, - = Center, o = Ball")
    print("+" + "-" * field_length + "+")
    for row in field:
        print("|" + ''.join(row) + "|")
    print("+" + "-" * field_length + "+")

# Wrapper function to build the field
def generate_minimap(left_team, right_team, ball_pos=None, field_length=60, field_width=10):
    field = create_field(field_width, field_length)
    
    # Place left team players
    for p in left_team:
        r, c = map_to_grid(p, field_length, field_width)
        if field[r][c] == ' ':
            field[r][c] = 'L'
        else:
            field[r][c] = '*'  # Overlap indicator
    
    # Place right team players
    for p in right_team:
        r, c = map_to_grid(p, field_length, field_width)
        if field[r][c] == ' ':
            field[r][c] = 'R'
        elif field[r][c] == 'L':
            field[r][c] = '*'  # Both teams overlap
        else:
            field[r][c] = 'R'
    
    # Place ball if position is provided
    if ball_pos is not None and ball_pos[0] is not None and ball_pos[1] is not None:
        r, c = map_to_grid(ball_pos, field_length, field_width)
        if field[r][c] == ' ':
            field[r][c] = 'o'
        else:
            # If ball overlaps with a player, show both
            field[r][c] = 'o'
    
    add_field_markings(field, field_length, field_width)
    return field 

def parse_ball_movement(obs):
    """Parse ball movement information including direction and speed.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        str: Description of ball movement (e.g., "Moving east at slow speed")
    """
    ball_direction = obs.get('ball_direction', None)
    ball_rotation = obs.get('ball_rotation', None)
    
    if ball_direction is None or len(ball_direction) < 2:
        return "Unknown movement"
    
    # Get x and y components of direction
    dx, dy = ball_direction[0:2]
    
    # Calculate speed (magnitude of velocity)
    # The direction vector is already normalized, so we need to get the actual velocity
    ball_velocity = obs.get('ball_velocity', None)
    if ball_velocity is not None and len(ball_velocity) >= 2:
        vx, vy = ball_velocity[0:2]
        speed = (vx**2 + vy**2)**0.5
    else:
        # Fallback to using direction magnitude if velocity not available
        speed = (dx**2 + dy**2)**0.5
    
    # Determine direction using 8-way compass
    # Calculate angle in degrees (0 is East, 90 is North)
    angle = math.degrees(math.atan2(-dy, dx))  # Negative dy because y is inverted
    # Normalize angle to 0-360
    angle = (angle + 360) % 360
    
    # Map angle to 8 directions
    if 337.5 <= angle or angle < 22.5:
        direction = "east"
    elif 22.5 <= angle < 67.5:
        direction = "northeast"
    elif 67.5 <= angle < 112.5:
        direction = "north"
    elif 112.5 <= angle < 157.5:
        direction = "northwest"
    elif 157.5 <= angle < 202.5:
        direction = "west"
    elif 202.5 <= angle < 247.5:
        direction = "southwest"
    elif 247.5 <= angle < 292.5:
        direction = "south"
    else:  # 292.5 <= angle < 337.5
        direction = "southeast"
    
    # Determine speed category with much lower thresholds
    if speed < 0.0001:  # Almost no movement
        speed_desc = "stationary"
    elif speed < 0.001:  # Very slow movement
        speed_desc = "very slow"
    elif speed < 0.003:  # Slow movement
        speed_desc = "slow"
    elif speed < 0.006:  # Moderate movement
        speed_desc = "moderate"
    elif speed < 0.01:   # Fast movement
        speed_desc = "fast"
    else:               # Very fast movement
        speed_desc = "very fast"
    
    # Add rotation information if available
    rotation_info = ""
    if ball_rotation is not None and len(ball_rotation) > 0:
        rot_x, rot_y = ball_rotation[0:2]
        if abs(rot_x) > 0.1 or abs(rot_y) > 0.1:
            rotation_info = " with spin"
    
    return f"Moving {direction} at {speed_desc} speed{rotation_info}" 

def get_player_direction(pos, player_direction):
    """Calculate player's movement direction based on direction vector.
    
    Args:
        pos (tuple): Player's position (x, y)
        player_direction (list): Direction vector [dx, dy]
        
    Returns:
        str: Direction description (e.g., "east", "northeast")
    """
    if player_direction is None or len(player_direction) < 2:
        return "stationary"
    
    dx, dy = player_direction[0:2]
    speed = (dx**2 + dy**2)**0.5
    
    if speed < 0.001:
        return "stationary"
    
    # Calculate angle in degrees (0 is East, 90 is North)
    angle = math.degrees(math.atan2(-dy, dx))  # Negative dy because y is inverted
    # Normalize angle to 0-360
    angle = (angle + 360) % 360
    
    # Map angle to 8 directions
    if 337.5 <= angle or angle < 22.5:
        return "east"
    elif 22.5 <= angle < 67.5:
        return "northeast"
    elif 67.5 <= angle < 112.5:
        return "north"
    elif 112.5 <= angle < 157.5:
        return "northwest"
    elif 157.5 <= angle < 202.5:
        return "west"
    elif 202.5 <= angle < 247.5:
        return "southwest"
    elif 247.5 <= angle < 292.5:
        return "south"
    else:  # 292.5 <= angle < 337.5
        return "southeast"

def get_player_speed(player_direction):
    """Calculate player's movement speed.
    
    Args:
        player_direction (list): Direction vector [dx, dy]
        
    Returns:
        str: Speed description (e.g., "walking", "running")
    """
    if player_direction is None or len(player_direction) < 2:
        return "stationary"
    
    dx, dy = player_direction[0:2]
    speed = (dx**2 + dy**2)**0.5
    
    speed *= 100
    if speed < 0.001:
        return "stationary"
    elif speed < 0.01:
        return "walking"
    elif speed < 0.02:
        return "jogging"
    elif speed < 0.03:
        return "running"
    else:
        return "sprinting"

def get_players_positions(obs):
    """Generate a dictionary of player positions and states.
    
    Args:
        obs (dict): The raw observation from the game environment.
        
    Returns:
        dict: Dictionary with keys in format "left_player_X" or "right_player_X"
              and values as strings describing player state
    """
    players = {}
    
    # Process left team
    left_team = obs.get('left_team', [])
    left_team_roles = obs.get('left_team_roles', [])
    left_team_direction = obs.get('left_team_direction', [])
    
    for i, (pos, role_id) in enumerate(zip(left_team, left_team_roles)):
        role = role_to_string(role_id)
        pos_desc = describe_ball_position(pos[0], pos[1])
        direction = left_team_direction[i] if i < len(left_team_direction) else None
        movement_dir = get_player_direction(pos, direction)
        speed = get_player_speed(direction)
        
        # Add special indicators
        indicators = []
        if i == obs.get('left_team_designated_player', -1):
            indicators.append("(designated)")
        if i in get_players_with_yellow_card(obs, "left"):
            indicators.append("(yellow card)")
        if i in get_players_with_red_card(obs, "left"):
            indicators.append("(red card)")
        
        indicators_str = " " + " ".join(indicators) if indicators else ""
        players[f"left_player_{i}"] = f"{role}: {pos_desc}, {speed} {movement_dir}{indicators_str}"
    
    # Process right team
    right_team = obs.get('right_team', [])
    right_team_roles = obs.get('right_team_roles', [])
    right_team_direction = obs.get('right_team_direction', [])
    
    for i, (pos, role_id) in enumerate(zip(right_team, right_team_roles)):
        role = role_to_string(role_id)
        pos_desc = describe_ball_position(pos[0], pos[1])
        direction = right_team_direction[i] if i < len(right_team_direction) else None
        movement_dir = get_player_direction(pos, direction)
        speed = get_player_speed(direction)
        
        # Add special indicators
        indicators = []
        if i == obs.get('right_team_designated_player', -1):
            indicators.append("(designated)")
        if i in get_players_with_yellow_card(obs, "right"):
            indicators.append("(yellow card)")
        if i in get_players_with_red_card(obs, "right"):
            indicators.append("(red card)")
        
        indicators_str = " " + " ".join(indicators) if indicators else ""
        players[f"right_player_{i}"] = f"{role}: {pos_desc}, {speed} {movement_dir}{indicators_str}"
    
    return players 