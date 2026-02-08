# data pre-processing

import pandas as pd

# read the dataset
df = pd.read_csv("smart_home_dataset.csv")
print(df.head())


def extract_state(row):
    return (int(row['Time']), int(row['User Activity']), int(row['Appliance State']))


actions = [0, 1]  # 0: turn off the light, 1: turn on the light

# define the reward function


def get_reward(user, device, price):
    if user == 1 and device == 0:
        return -3
    elif user == 1 and device == 1:
        return -price
    elif user == 0 and device == 1:
        return -price - 0.5
    else:
        return 2


def get_next_state(index, df, action):
    if index + 1 >= len(df):
        return None  # End

    next_row = df.iloc[index + 1]
    return (int(next_row['Time']),
            int(next_row['User Activity']),
            action)  # the new state is from electricity

def simulate_step(index, df, action):
    row = df.iloc[index]
    state = extract_state(row)
    electricity_price = row['Electricity Price']
    user_activity = row['User Activity']
    
    reward = get_reward(user_activity, action, electricity_price)
    next_state = get_next_state(index, df, action)
    
    return state, action, reward, next_state

# define the Qlearning Agent to fix our reinforement

import numpy as np
from collections import defaultdict

class QLearningAgent: 
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = defaultdict(lambda: np.zeros(len(actions)))
        self.actions = actions
        self.alpha = alpha            # learning rate
        self.gamma = gamma            # gamma
        self.epsilon = epsilon        # explosive

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.choice(self.actions)  #action decision
        else:
            return np.argmax(self.q_table[state])  # action!

    def learn(self, state, action, reward, next_state):
        predict = self.q_table[state][action]
        if next_state is not None:
            target = reward + self.gamma * np.max(self.q_table[next_state])
        else:
            target = reward  # non next state for reward
        self.q_table[state][action] += self.alpha * (target - predict)

# This is the Training

from tqdm import tqdm
agent = QLearningAgent(actions=[0, 1], alpha=0.001, gamma=0.95, epsilon=0.02)

initial_epsilon = 0.3
min_epsilon = 0.005
decay_rate = 0.995

num_epochs = 3000
reward_history = []

for epoch in tqdm(range(num_epochs), desc="Training Progress"):
    epoch_reward = 0

    # 調整探索率（epsilon decay）
    agent.epsilon = max(min_epsilon, initial_epsilon * (decay_rate ** epoch))

    for i in range(len(df) - 1):
        row = df.iloc[i]
        state = extract_state(row)
        action = agent.choose_action(state)
        next_state = get_next_state(i, df, action)
        reward = get_reward(row['User Activity'], action, row['Electricity Price'])

        agent.learn(state, action, reward, next_state)
        epoch_reward += reward

    reward_history.append(epoch_reward)


# to check the great movement in some hours.
for hour in range(24):
    for user in [0, 1]:
        for device in [0, 1]:
            state = (hour, user, device)
            q_values = agent.q_table[state]
            best_action = np.argmax(q_values)
            print(f"State: {state}, Q-values: {q_values}, Best Action: {best_action}")


# Visulize the Agent
def test_agent(agent, df, verbose=False):
    total_reward = 0
    decisions = []

    for i in range(len(df) - 1):
        row = df.iloc[i]
        state = extract_state(row)
        action = agent.choose_action(state)

        reward = get_reward(row['User Activity'], action, row['Electricity Price'])
        total_reward += reward
        decisions.append((state, action, reward))

        if verbose:
            print(f"Step {i}: State={state}, Action={action}, Reward={reward}")

    return total_reward, decisions


import matplotlib.pyplot as plt

plt.plot(reward_history)
plt.xlabel('Epoch')
plt.ylabel('Total Reward')
plt.title('Reward Trend during Training')
plt.grid(True)
plt.show()


import random

def random_strategy(df):
    total_reward = 0
    for i in range(len(df) - 1):
        action = random.choice([0, 1])
        row = df.iloc[i]
        reward = get_reward(row['User Activity'], action, row['Electricity Price'])
        total_reward += reward
    return total_reward

# 執行比較
trained_reward, _ = test_agent(agent, df)
random_reward = random_strategy(df)

print(f"🧠 Agent (訓練後) 總 Reward: {trained_reward}")
print(f"🎲 Random Agent 總 Reward: {random_reward}")

# 4

import matplotlib.pyplot as plt
import pandas as pd

# 建立策略紀錄列表
policy_map = []

for time in range(24):
    for user_activity in [0, 1]:
        for device_state in [0, 1]:
            state = (time, user_activity, device_state)
            if state in agent.q_table:
                q_values = agent.q_table[state]
                best_action = int(np.argmax(q_values))
                policy_map.append({
                    'Time': time,
                    'UserActivity': user_activity,
                    'ApplianceState': device_state,
                    'BestAction': best_action
                })

# DataFrame
df_policy = pd.DataFrame(policy_map)

# 繪圖：不同使用者情境與裝置狀態下的動作策略
fig, ax = plt.subplots(figsize=(12, 6))
for key, grp in df_policy.groupby(['UserActivity', 'ApplianceState']):
    label = f"User={key[0]}, Device={key[1]}"
    ax.plot(grp['Time'], grp['BestAction'], label=label, marker='o')

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Best Action (0=Off, 1=On)")
ax.set_title("Agent's Learned Policy (from Loaded Q-table)")
ax.legend()
plt.grid(True)
plt.show()

import pickle

# and also you can save the Q-table file
with open('q_table.pkl', 'wb') as f:
    pickle.dump(dict(agent.q_table), f)

# and load the Q-table
with open('q_table.pkl', 'rb') as f:
    q_data = pickle.load(f)
    agent.q_table = defaultdict(lambda: np.zeros(2), q_data)
    
