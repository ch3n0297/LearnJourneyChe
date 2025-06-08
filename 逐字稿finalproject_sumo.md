**Slide 1: Sumo Final Progress**

Hello everyone, thank you for being here today. This is our final project presentation for the SUMO simulation course. In this presentation, we will walk you through the progress we've made, the challenges we encountered, and the insights we gained while working on our traffic optimization project using Q-Learning within the SUMO environment.

We aim to demonstrate how reinforcement learning can be used to improve urban traffic efficiency and how simulation tools like SUMO can support intelligent transportation systems research. Let's get started!

**Slide 2: Project Overview**

Our project focuses on developing a traffic signal control system using Q-Learning, a type of reinforcement learning. The goal is to reduce traffic congestion and waiting time by dynamically adjusting traffic lights based on the traffic conditions.

We use the SUMO (Simulation of Urban Mobility) environment to simulate a realistic traffic network, where agents—representing traffic signals—learn optimal actions by interacting with the environment over many episodes.

In the following slides, we will explain the system architecture, training process, evaluation metrics, and our final results.

**Slide 3: System Architecture**

The system is composed of several key components: the SUMO simulator, a Python-based control script, and the Q-Learning agent. We integrate these using the TraCI (Traffic Control Interface) protocol.

Each traffic light is treated as an independent agent that observes the current traffic state—such as the number of waiting vehicles—and selects an action, such as changing the signal phase. The agent then receives a reward based on the outcome, typically tied to metrics like waiting time or queue length.

Over time, the agent learns a Q-table that maps observed states to optimal actions. This enables it to make better decisions in future episodes.

**Slide 4: Training Setup**

For training, we defined a simplified traffic network with multiple intersections and variable vehicle flows. The environment is reset for each episode, and the agent is allowed to take actions over a fixed number of simulation steps.

We used an ε-greedy exploration strategy, gradually shifting from random actions to exploitation of the learned policy. The reward function penalizes long wait times and frequent signal switching, while rewarding smoother traffic flow.

Training was conducted over several hundred episodes, with performance metrics logged at each interval. This allowed us to evaluate learning progress and adjust hyperparameters such as learning rate and discount factor.

**Slide 5: Evaluation Metrics**

To evaluate the effectiveness of our traffic control policy, we focused on several key metrics:

1. **Average Waiting Time** – the mean time vehicles spent stopped at intersections.
    
2. **Queue Length** – the number of vehicles waiting in line at each phase.
    
3. **Total Trip Duration** – the time taken for vehicles to travel from origin to destination.
    
4. **Traffic Flow** – the number of vehicles successfully passing through the junctions.
    

We compared these metrics before and after training to assess the improvement. The results indicated that our Q-Learning-based system significantly reduced congestion and improved traffic flow across the simulated network.

**Slide 6: Results and Observations**

After training the Q-Learning agent, we observed a consistent reduction in average waiting time and queue length. Vehicles were able to move more smoothly through the intersections, resulting in a more balanced flow.

In particular, intersections controlled by trained agents showed faster clearance times compared to those using fixed-time signals. We also noticed that the agent was able to adapt to changing traffic patterns, improving performance during both peak and off-peak periods.

However, we also encountered limitations. The Q-table grows large with complex state representations, making generalization difficult. Additionally, some extreme congestion scenarios were not fully resolved due to limited training exposure.

Despite these challenges, the overall improvement was promising and confirmed the potential of reinforcement learning in traffic signal control.

**Slide 7: Future Improvements**

Looking ahead, there are several ways we can enhance the system:

1. **State Representation** – Introduce more abstract or continuous features, or apply dimensionality reduction to manage Q-table complexity.
    
2. **Multi-Agent Coordination** – Enable collaboration between traffic lights to handle network-level optimization instead of independent learning.
    
3. **Deep Q-Network (DQN)** – Replace the Q-table with neural networks to allow generalization to unseen states and support scalability.
    
4. **Real-world Data Integration** – Use actual traffic data to train and validate the agent's decision-making process.
    

These improvements would allow our model to better handle complex, dynamic urban environments and support real-world deployment in intelligent traffic systems.

**Slide 8: Conclusion**

In conclusion, our project demonstrated the feasibility of using Q-Learning for adaptive traffic signal control in a simulated urban environment. Through careful design of the reward function, state-action space, and training process, we were able to improve traffic flow and reduce congestion.

The results validate the potential of reinforcement learning in traffic management. While challenges remain, especially with scalability and real-world deployment, we believe this approach lays a strong foundation for future research and applications.

Thank you for your attention. We’re happy to answer any questions you may have.