from parking_environment import ParkingEnvironment
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

env = ParkingEnvironment()

check_env(env)

model = PPO("MultiInputPolicy", env, verbose=1)

print("start training")

model.learn(total_timesteps=300_000)

model.save("models/my_custom_ppo_agent")
print("model saved")

env.close()

eval_env = ParkingEnvironment(render_mode="human")

# Load the model
loaded_model = PPO.load("models/my_custom_ppo_agent")

# Enjoy the trained agent!
obs, info = eval_env.reset()
eval_env.render()
for i in range(10000):
    # The agent predicts the best action based on the current observation
    action, _states = loaded_model.predict(obs, deterministic=True)
    
    # The environment takes a step based on the action
    obs, reward, terminated, truncated, info = eval_env.step(action)

    eval_env.render()
    
    # If the episode is over (success or failure), reset the environment
    if terminated or truncated:
        obs, info = eval_env.reset()

eval_env.close()