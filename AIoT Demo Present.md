

> Hello everyone, today I’d like to introduce my smart home project using Q-Learning.  

---

### Step 1: Data Preprocessing

> First, I loaded the dataset using Pandas.  
> Each data row includes the time, user activity, the state of the appliance, and the electricity price.

> I then defined a function to extract the **state**, which is a tuple of:
> 
> - the current hour,
>     
> - whether the user is present,
>     
> - and whether the appliance is currently on or off.
>     
```python
import pandas as pd

# read the dataset
df = pd.read_csv("smart_home_dataset.csv")
print(df.head())

def extract_state(row):
    return (int(row['Time']), int(row['User Activity']), int(row['Appliance State']))
```
---

### Step 2: Reward Function

> At first, I designed a very aggressive reward function.  
> If the user was at home and the light was off, I penalized the agent with **-10(minus 10)**.  
> And if the device was on while nobody was home, I subtracted even more.  
> However, this made the agent too conservative — it ended up just keeping the device **always on** to avoid high penalties.

> After several trials, I redesigned the reward function to be more balanced.  
> Now:
> 
> - If the user is home and the device is off, the penalty is **-3** (more reasonable).
>     
> - If the device is on, we subtract the electricity price.
>     
> - And if no one is home but the light is on, we subtract the price **plus 0.5** as an extra penalty.
>     
> - If the light is off and no one is home, we reward **+2** to encourage energy saving.
>     

> This new version helped the agent learn a better strategy, where it doesn’t just play safe — it actually tries to **adapt to time and user behavior**.
>     

---

### Step 3: Q-Learning Agent

> I implemented the core logic of reinforcement learning by defining a `QLearningAgent` class.

---

###  `__init__` – Initialization

```python
self.q_table = defaultdict(lambda: np.zeros(len(actions)))
```

> I use a `defaultdict` to store the Q-values. Each state maps to a list of action values, initialized as zeros.  
> This means that when the agent encounters a new state for the first time, it starts with equal values for all actions.

```python
self.alpha = alpha
self.gamma = gamma
self.epsilon = epsilon
```

|Parameter|Meaning|
|---|---|
|**alpha**|Learning rate: how quickly we update our Q-values|
|**gamma**|Discount factor: how much we care about future rewards|
|**epsilon**|Exploration rate: the probability of taking a random action|

> These values help balance exploration vs exploitation and learning speed.

---

### `choose_action(self, state)`

```python
if np.random.rand() < self.epsilon:
    return np.random.choice(self.actions)
else:
    return np.argmax(self.q_table[state])
```

> This is the **ε-greedy decision rule**.  
> With a small chance `epsilon`, the agent explores by choosing a random action.  
> Most of the time, it chooses the action with the **highest Q-value**, which represents the best option learned so far.

---

`learn(self, state, action, reward, next_state)`

```python
predict = self.q_table[state][action]
if next_state is not None:
    target = reward + self.gamma * np.max(self.q_table[next_state])
else:
    target = reward
```

> Here, the agent uses the **Bellman equation** to calculate a new target Q-value.  
> If there is a next state, it adds the **discounted best future value** to the reward.  
> If it's the last step, the target is just the reward itself.

```python
self.q_table[state][action] += self.alpha * (target - predict)
```

> This line updates the Q-table using the **difference between prediction and target**, scaled by the learning rate.


> My QLearningAgent stores Q-values in a table, decides actions using an ε-greedy policy, and updates its knowledge using the Bellman equation.  
> Over time, this agent learns the best actions for different situations by maximizing expected reward.

```python
class QLearningAgent: 
    def __init__(self, actions, alpha, gamma, epsilon):
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
```

---

### Step 4: Training the Agent

> I trained the agent over **3000 epochs**.  
> In each epoch, the agent:
> 
> 1. reads the current state from the dataset,
>     
> 2. chooses an action (turn on or off),
>     
> 3. receives a reward, and
>     
> 4. updates the Q-table.

In this offline Q-Learning setup, the term "epoch" refers to one complete iteration through the dataset. Although this differs from the typical use of "episode" in online reinforcement learning, it is a practical usage when training on static data.

> I also added **epsilon decay**, so it explores more in early training and becomes more stable later on.
```python
from tqdm import tqdm
	agent = QLearningAgent(actions=[0, 1],alpha=0.001,gamma=0.95,epsilon=0.02)

initial_epsilon = 0.3
min_epsilon = 0.005
decay_rate = 0.995

num_epochs = 3000
reward_history = []

for epoch in tqdm(range(num_epochs), desc="Training Progress"):
    epoch_reward = 0

    #epsilon decay
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
```
---

### 🟪 Step 5: Evaluation & Visualization

> In this step, I evaluate how well the Q-Learning agent performed after training.

---

① Reward Trend Plot (Training Performance)

> The chart on the left shows the **total reward per epoch** over 3000 training iterations.  
> You can see that the agent starts with low and unstable performance, but quickly improves and stabilizes above **+550 total reward**.  
> This means the agent is learning consistently and the Q-table is converging.

This function simulates a random agent.  
For every step in the dataset, it randomly picks either `0` or `1` — that is, turn the device off or on — without any learning or memory.

---

② Policy Map (Action Strategy by Time)

> The graph on the right is the **strategy map**, showing which action the agent prefers for each situation and time of day.

- Y-axis shows the action: `0 = Off`, `1 = On`
    
- X-axis shows the hour of the day (0 to 23)
    
- Each colored line represents a different context:
    
    - 🔵 **User=0, Device=0**: Agent correctly keeps it off
        
    - 🟠 **User=0, Device=1**: Agent learns to turn it off for energy saving
        
    - 🟢 **User=1, Device=0**: The agent chooses to turn it on in most hours, which reflects user comfort
        
    - 🔴 **User=1, Device=1**: Agent keeps the device on, maintaining comfort unless the context suggests otherwise
        

> These results show that the agent learned to behave differently depending on **time and user presence**, instead of applying a fixed rule.

---

### 📊 ③ Performance Comparison

|Strategy|Total Reward|
|---|---|
|**Trained Agent**|`+288.7` ✅|
|**Random Policy**|`-298.3` ❌|

> Compared to a random decision-making agent, the trained agent performs **over 580 points better** in total reward, clearly showing it has learned a meaningful and effective control policy.
```python
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

print(f"Agent (Pre-trained) Reward: {trained_reward}")
print(f"Random Agent Reward: {random_reward}")
```

---

### ✅ Summary for this section:

> The agent has successfully learned a time-sensitive and user-aware behavior strategy. It optimizes appliance usage to reduce cost and maintain comfort, and performs much better than a random baseline.

---

如果你需要我幫你這段整理成：

- Markdown 段落（可以用在 Typora 或簡報筆記）
    
- PowerPoint Slide 模板（含表格與圖說格式）
    
- 中英文對照說法（如果老師或觀眾是雙語）
    

我都可以幫你一次完成。需要我幫你整理到哪個格式呢？
---

### 📊 Step 6: Policy Visualization

> Finally, This **strategy map** visualize the agent’s decisions across different times and situations.  
> It shows, for example, that the agent tends to turn off the appliance when no one is home, and keeps it on when the user is active.

---

### ✅ Conclusion

> In summary, my Q-Learning agent successfully learned to manage smart home appliances in a way that balances electricity cost and user comfort.  
> Thank you for listening!
