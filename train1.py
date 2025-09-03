import gymnasium as gym
import numpy as np
import random
from stable_baselines3 import PPO
from gymnasium import spaces
import os

class DroneAvoidanceEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super().__init__()
        self.WIDTH, self.HEIGHT = 800, 600
        self.DRONE_W, self.DRONE_H = 40, 40
        self.drone_x = 100
        self.drone_y = self.HEIGHT // 2
        self.obstacles = []
        self.spawn_interval = 45  # Slightly slower spawns for easier start
        self.spawn_timer = 0
        self.step_count = 0
        self.action_space = spaces.Discrete(3)  # 0=up, 1=stay, 2=down
        self.max_obstacles = 7  # Enough to avoid late observation
        self.observation_space = spaces.Box(
            low=0,
            high=1,
            shape=(3 + self.max_obstacles * 5,),  # {drone_y, vel_y, distance_to_center, obstacle_x, obstacle_y, obstacle_w, obstacle_h, obstacle_v}
            dtype=np.float32
        )
        self.prev_y = self.HEIGHT // 2

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.drone_y = self.HEIGHT // 2
        self.obstacles = []
        self.spawn_timer = 0
        self.step_count = 0
        self.prev_y = self.HEIGHT // 2
        return self.get_obs(), {}

    def spawn_obstacle(self):
        w, h = random.choice([(50, 50), (80, 30), (30, 80)])
        y = np.random.randint(0, self.HEIGHT - h)
        speed = np.random.uniform(2, 5)
        self.obstacles.append([self.WIDTH, y, w, h, speed])

    def step(self, action):
        self.step_count += 1

        # Save previous y for velocity calculation
        prev_y = self.drone_y

        # Execute action
        if action == 0:  # up
            self.drone_y = max(0, self.drone_y - 12)
        elif action == 2:  # down
            self.drone_y = min(self.HEIGHT - self.DRONE_H, self.drone_y + 12)

        # Spawn obstacles
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = self.spawn_interval
        else:
            self.spawn_timer -= 1

        # Move obstacles and check collisions & risk
        new_obstacles = []
        terminated = False
        risk_penalty = 0
        for obs in self.obstacles:
            x, y, w, h, s = obs
            x -= s
            if (self.drone_x < x + w and self.drone_x + self.DRONE_W > x and
                self.drone_y < y + h and self.drone_y + self.DRONE_H > y):
                terminated = True
            if x + w > 0:
                new_obstacles.append([x, y, w, h, s])
                # Calculate distance between drone and obstacle center
                drone_center = self.drone_y + self.DRONE_H/2
                obs_center = y + h/2
                dy = abs(drone_center - obs_center)
                if dy < (self.DRONE_H + h)/2:
                    risk_penalty += (100 - dy * 2)
        self.obstacles = new_obstacles

        # Survival reward and risk/collision penalty
        reward = 2  # Increased survival bonus
        if terminated:
            reward = -300  # Large penalty for collision
        else:
            # Add risk penalty (less if no risk)
            reward -= min(10, risk_penalty * 0.02)
            # Add small penalty for being off-center (smooths path, not too strong)
            reward -= abs(self.drone_y - (self.HEIGHT//2)) * 0.01

        # Penalize jerkiness (rapid vertical changes)
        vel_y = abs(self.drone_y - prev_y)
        reward -= vel_y * 0.03  # Penalty for rapid movement

        # Increase difficulty gradually
        if self.step_count % 2000 == 0:
            self.spawn_interval = max(20, self.spawn_interval - 2)

        obs = self.get_obs()
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

    def get_obs(self):
        # Drone features: y, dy/dt, distance to center (normalized)
        normalized_y = (self.drone_y / self.HEIGHT)
        vel_y = (self.drone_y - self.prev_y) / self.HEIGHT
        dist_to_center = abs(self.drone_y - (self.HEIGHT//2)) / (self.HEIGHT//2)
        obs = [normalized_y, vel_y, dist_to_center]
        for i in range(self.max_obstacles):
            if i < len(self.obstacles):
                x, y, w, h, s = self.obstacles[i]
                # Normalized features: x, y, w, h, speed
                normalized_x = x / self.WIDTH
                normalized_y = y / self.HEIGHT
                normalized_w = w / self.WIDTH
                normalized_h = h / self.HEIGHT
                normalized_s = s / 5.0  # Max speed is 5
                obs.extend([normalized_x, normalized_y, normalized_w, normalized_h, normalized_s])
            else:
                obs.extend([0, 0, 0, 0, 0])
        self.prev_y = self.drone_y
        return np.array(obs, dtype=np.float32)

def train_drone_agent():
    env = DroneAvoidanceEnv()
    # Optimized PPO parameters for smoother, safer learning
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=4096,
        batch_size=256,
        n_epochs=10,
        gamma=0.96,        # Focus on near-term rewards
        ent_coef=0.02,     # Encourage exploration
        clip_range=0.2,
    )
    model.learn(total_timesteps=1_000_000)
    model.save("drone_ppo_model_improved")
    print("\nTraining complete! Model saved as 'drone_ppo_model_improved.zip'")

if __name__ == "__main__":
    train_drone_agent()

