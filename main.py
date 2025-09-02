from flask import Flask, render_template_string
from flask_socketio import SocketIO
import random
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game settings
WIDTH, HEIGHT = 800, 600
DRONE_W, DRONE_H = 40, 40
DRONE_SPEED = 5
MAX_SPEED = 12
MIN_SPAWN = 300
SCROLL_SPEED = 2

# Game state
drone_y = HEIGHT // 2 - DRONE_H // 2
obstacles = []
score = 0
level = 1
SPAWN_INTERVAL = 1.2  # seconds
last_spawn = 0
game_over = False
bg_x = 0

OBSTACLE_TYPES = [
    {"size": (50, 50), "speed": 4},
    {"size": (80, 30), "speed": 3},
    {"size": (30, 80), "speed": 5},
]

# Colors
DARK_BG = "#0D1117"
CYAN = "#00FFFF"
WHITE = "#FFFFFF"
GRAY = "#323232"

def spawn_obstacle():
    obs_type = random.choice(OBSTACLE_TYPES)
    w, h = obs_type["size"]
    y = random.randint(0, HEIGHT - h)
    speed = min(obs_type["speed"], MAX_SPEED)
    obstacles.append({"x": WIDTH, "y": y, "w": w, "h": h, "speed": speed})

def find_best_path():
    safe_zones = [(0, HEIGHT)]
    look_ahead = WIDTH + 300
    upcoming = [o for o in obstacles if o["x"] < look_ahead]
    for obs in upcoming:
        new_safe = []
        for (start, end) in safe_zones:
            obs_top, obs_bottom = obs["y"], obs["y"] + obs["h"]
            if obs_top > start and obs_bottom < end:
                new_safe.append((start, obs_top))
                new_safe.append((obs_bottom, end))
            elif obs_top <= start < obs_bottom < end:
                new_safe.append((obs_bottom, end))
            elif start < obs_top < end <= obs_bottom:
                new_safe.append((start, obs_top))
            elif obs_bottom <= start or obs_top >= end:
                new_safe.append((start, end))
        safe_zones = new_safe
    if not safe_zones:
        return None
    best_zone = max(safe_zones, key=lambda z: z[1] - z[0])
    best_y = (best_zone[0] + best_zone[1]) // 2 - DRONE_H // 2
    if abs(best_y - drone_y) < DRONE_SPEED:
        return best_y
    return drone_y + DRONE_SPEED if best_y > drone_y else drone_y - DRONE_SPEED

def reset_game():
    global drone_y, obstacles, score, level, SPAWN_INTERVAL, game_over, bg_x
    drone_y = HEIGHT // 2 - DRONE_H // 2
    obstacles.clear()
    score = 0
    level = 1
    SPAWN_INTERVAL = 1.2
    game_over = False
    bg_x = 0

def game_loop():
    global drone_y, obstacles, score, level, SPAWN_INTERVAL, game_over, last_spawn, bg_x
    while True:
        if not game_over:
            now = time.time()
            # Spawn obstacles
            if now - last_spawn >= SPAWN_INTERVAL:
                spawn_obstacle()
                last_spawn = now
            # Move obstacles
            for o in obstacles[:]:
                o["x"] -= o["speed"]
            obstacles = [o for o in obstacles if o["x"] + o["w"] > 0]
            # Drone AI
            best_y = find_best_path()
            if best_y is not None:
                drone_y = best_y
            drone_y = max(0, min(HEIGHT - DRONE_H, drone_y))
            # Collision
            for o in obstacles:
                if (100 < o["x"] + o["w"] and 100 + DRONE_W > o["x"] and
                    drone_y < o["y"] + o["h"] and drone_y + DRONE_H > o["y"]):
                    game_over = True
            # Score and level
            if not game_over:
                score += 1
                if score % 5000 == 0:
                    level += 1
                    for t in OBSTACLE_TYPES:
                        t["speed"] = min(t["speed"] + 0.5, MAX_SPEED)
                    SPAWN_INTERVAL = max(MIN_SPAWN / 1000, SPAWN_INTERVAL - 0.05)
            # Background scroll
            bg_x = (bg_x - SCROLL_SPEED) % WIDTH
            # Broadcast state to all clients
            socketio.emit('update', {
                'drone_y': drone_y,
                'obstacles': obstacles,
                'score': score,
                'level': level,
                'game_over': game_over,
                'bg_x': bg_x,
            })
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Drone Dodger (Dark & Cyan)</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body { margin: 0; background: #0D1117; font-family: monospace; color: #00FFFF; }
        canvas { display: block; margin: 0 auto; background: #0D1117; }
        #ui { position: absolute; top: 10px; left: 10px; }
        #level { position: absolute; top: 10px; right: 10px; }
    </style>
</head>
<body>
    <div id="ui">Score: <span id="score">0</span></div>
    <div id="level">Level: <span id="levelValue">1</span></div>
    <canvas id="gameCanvas" width="800" height="600"></canvas>
    <script>
        const socket = io();
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const DARK_BG = '#0D1117';
        const CYAN = '#00FFFF';
        const WHITE = '#FFFFFF';
        const GRAY = '#323232';

        socket.on('update', (data) => {
            // Clear canvas
            ctx.fillStyle = DARK_BG;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            // Draw background bands
            ctx.fillStyle = GRAY;
            ctx.fillRect(data.bg_x, 0, canvas.width, canvas.height);
            ctx.fillRect(data.bg_x + canvas.width, 0, canvas.width, canvas.height);
            // Draw obstacles
            ctx.fillStyle = WHITE;
            data.obstacles.forEach(o => {
                ctx.fillRect(o.x, o.y, o.w, o.h);
            });
            // Draw drone (cyan)
            ctx.fillStyle = CYAN;
            ctx.fillRect(100, data.drone_y, {{DRONE_W}}, {{DRONE_H}});
            // Update UI
            document.getElementById('score').textContent = data.score;
            document.getElementById('levelValue').textContent = data.level;
            // Game over
            if (data.game_over) {
                ctx.fillStyle = WHITE;
                ctx.font = '24px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('AI FAILED! Refresh to restart', canvas.width/2, canvas.height/2);
            }
        });
        // Reset on R key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'r') socket.emit('reset');
        });
    </script>
</body>
</html>
'''.replace('{{DRONE_W}}', str(DRONE_W)).replace('{{DRONE_H}}', str(DRONE_H)))

@socketio.on('reset')
def handle_reset():
    reset_game()

if __name__ == '__main__':
    threading.Thread(target=game_loop, daemon=True).start()
    socketio.run(app, debug=True)
