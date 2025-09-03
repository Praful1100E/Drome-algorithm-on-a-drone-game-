import os
import time
import threading
import numpy as np
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from stable_baselines3 import PPO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, async_mode='threading')

# --- Game Settings ---
WIDTH, HEIGHT = 800, 600
DRONE_W, DRONE_H = 40, 40
DRONE_X = 100
DRONE_SPEED = 8
MAX_SPEED = 14
MIN_SPAWN = 300  # milliseconds
BG_SCROLL = 2

# --- Load Trained RL Model ---
model_path = "drone_ppo_model_improved.zip"
if not os.path.exists(model_path):
    raise FileNotFoundError("RL model 'drone_ppo_model.zip' not found in current folder.")
model = PPO.load(model_path)

# --- Game State ---
drone = {'y': HEIGHT // 2 - DRONE_H // 2, 'score': 0, 'level': 1, 'game_over': False}
obstacles = []
bg_x = 0
spawn_timer = 0
SPAWN_INTERVAL = 1.2  # seconds

# --- Obstacle Types ---
OBSTACLE_TYPES = [
    {'w': 50, 'h': 50, 'speed': 4},
    {'w': 80, 'h': 30, 'speed': 3},
    {'w': 30, 'h': 80, 'speed': 5},
]

# --- Helper Functions ---
def spawn_obstacle():
    obs = random.choice(OBSTACLE_TYPES)
    y = np.random.randint(0, HEIGHT - obs['h'])
    obstacles.append({
        'x': WIDTH, 'y': y, 'w': obs['w'], 'h': obs['h'], 'speed': obs['speed']
    })

def reset_game():
    global drone, obstacles, bg_x, spawn_timer
    drone = {'y': HEIGHT // 2 - DRONE_H // 2, 'score': 0, 'level': 1, 'game_over': False}
    obstacles = []
    bg_x = 0
    spawn_timer = 0

def prepare_observation():
    obs = [drone['y'], DRONE_X]
    for i in range(10):  # max_obstacles = 10
        if i < len(obstacles):
            obs.extend([obstacles[i][key] for key in ['x', 'y', 'w', 'h']])
        else:
            obs.extend([0, 0, 0, 0])
    return np.array(obs, dtype=np.float32)

def game_loop():
    global drone, obstacles, bg_x, spawn_timer
    while True:
        if not drone['game_over']:
            # Spawn obstacles
            if spawn_timer <= 0:
                spawn_obstacle()
                spawn_timer = int(SPAWN_INTERVAL * 30)
            else:
                spawn_timer -= 1
            # Move obstacles
            for o in obstacles[:]:
                o['x'] -= o['speed']
            obstacles[:] = [o for o in obstacles if o['x'] + o['w'] > 0]
            # RL decision
            obs = prepare_observation()
            action, _ = model.predict(obs)
            if action == 0:  # up
                drone['y'] = max(0, drone['y'] - DRONE_SPEED)
            elif action == 2:  # down
                drone['y'] = min(HEIGHT - DRONE_H, drone['y'] + DRONE_SPEED)
            # Collision detection
            for o in obstacles:
                if (DRONE_X < o['x'] + o['w'] and DRONE_X + DRONE_W > o['x'] and
                    drone['y'] < o['y'] + o['h'] and drone['y'] + DRONE_H > o['y']):
                    drone['game_over'] = True
            if not drone['game_over']:
                drone['score'] += 1
                if drone['score'] % 5000 == 0:
                    drone['level'] += 1
                    # Increase difficulty
                    for t in OBSTACLE_TYPES:
                        t['speed'] = min(t['speed'] + 0.5, MAX_SPEED)
                    spawn_interval = max(MIN_SPAWN / 1000, SPAWN_INTERVAL - 0.05)
            # Background scroll
            bg_x = (bg_x - BG_SCROLL) % WIDTH
            # Emit state to all clients
            socketio.emit('update', {
                'drone': drone,
                'obstacles': obstacles,
                'bg_x': bg_x,
            })
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
<title>RL Drone Simulator</title>
<style>
body { margin:0; background:#0D1117; color:#00FFFF; font-family:monospace; }
canvas { display:block; margin:0 auto; background:#0D1117; box-shadow:0 0 16px #00FFFF33; }
#ui { position:absolute; top:10px; left:10px; font-weight:bold; font-size:1.2rem; }
#level { position:absolute; top:10px; right:10px; font-weight:bold; font-size:1.2rem; }
</style>
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
<div id="ui">Score: <span id="score">0</span></div>
<div id="level">Level: <span id="levelValue">1</span></div>
<canvas id="gameCanvas" width="800" height="600"></canvas>
<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const DARK_BG = "#0D1117";
const CYAN = "#00FFFF";
const WHITE = "#FFFFFF";
const GRAY = "#323232";

const socket = io();
socket.on('update', function(data) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = DARK_BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = GRAY;
    ctx.fillRect(data.bg_x, 0, canvas.width, canvas.height);
    ctx.fillRect(data.bg_x + canvas.width, 0, canvas.width, canvas.height);
    ctx.fillStyle = WHITE;
    data.obstacles.forEach(o => {
        ctx.fillRect(o.x, o.y, o.w, o.h);
    });
    ctx.fillStyle = CYAN;
    ctx.fillRect(100, data.drone.y, 40, 40);
    document.getElementById("score").textContent = data.drone.score;
    document.getElementById("levelValue").textContent = data.drone.level;
    if (data.drone.game_over) {
        ctx.fillStyle = WHITE;
        ctx.font = "24px monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("Game Over! Refresh to restart", canvas.width/2, canvas.height/2);
    }
});
document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'r' && window.confirm('Restart simulation?')) {
        socket.emit('reset');
    }
});
</script>
</body>
</html>''')

@socketio.on('reset')
def handle_reset():
    reset_game()

if __name__ == "__main__":
    import random
    threading.Thread(target=game_loop, daemon=True).start()
    socketio.run(app, debug=True)
