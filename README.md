# AI Car Parking Simulation 🚗🧠

## About the Project
This project is a custom Reinforcement Learning environment where an artificial intelligence agent attempts to learn how to park a car in a designated spot. 

Instead of hard-coding the car's movements, the agent learns through trial and error, receiving "rewards" or "penalties" based on its actions. The custom environment was built to simulate vehicle physics and boundaries, providing a visual representation of the machine learning process in real-time.

## Technologies Used
* **Python:** Core programming language.
* **Gymnasium:** Used to build the custom reinforcement learning environment and manage the state/action spaces.
* **Pygame:** Handled the 2D visualization and rendering of the car, parking lot, and obstacles.
* **PPO (Proximal Policy Optimization):** The reinforcement learning algorithm used to train the agent.

## Current Status & Known Limitations
The environment, physics, and training loop are fully operational. The AI successfully explores the environment, understands basic movement, and attempts to navigate toward the parking spot. 

**Current Focus:** The agent currently struggles to execute a *perfect* parking maneuver. This is due to the current reward function design. My active next steps involve re-engineering the reward system (e.g., heavily penalizing collisions while rewarding precise alignment and stopping within the lines) to improve the final parking accuracy.