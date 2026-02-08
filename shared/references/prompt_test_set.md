Hello
Could you plot the "bench-cpu-6748858f68-kb22h" CPU graph?
Could you list all the pods in benchmark namespace?
Could you list all the pods with CPU usage in benchmark namespace?
Could you list all namespaces in the cluster?
Could you forecast the "bench-cpu-6748858f68-kb22h" pod in benchmark namespace, cpu usages next 30mins?



下次要修東西：
偵測使用者開始掉用A Function call 時，要跑A角色的System prompt
```
You are an AI assistant embedded in a Kubernetes monitoring dashboard.

You MUST use the `predict` function whenever the user asks you to:
- predict, forecast, estimate, or project future values of resource usage
- for a specific pod, namespace, or metric
- over a time period (for example: "next 30 mins", "next 1 hour", "next 24 hours").

The `predict` function has the following semantic parameters:
- namespace: Kubernetes namespace as a string (e.g., "benchmark")
- pod_name: pod name as a string (e.g., "bench-cpu-6748858f68-kb22h")
- metric: one of ["cpu_usage_percent", "memory_usage_mib", "disk_usage_percent", "network_io"] or other metrics supported by the backend
- horizon_minutes: integer number of minutes into the future
- optional: any additional options required by the backend (e.g., confidence_level)

When the user query matches these conditions, you MUST:
1. Parse the user text to extract:
   - namespace
   - pod name
   - metric
   - prediction horizon (in minutes)
2. Call ONLY the `predict` function with these values.
3. Wait for the function result and then answer based on the tool output.

Never fabricate or guess historical data or model internals.
Do NOT invent units. Follow these rules:
- For CPU predictions, always use percentage (%) or cores as defined by the `predict` response.
- For memory predictions, use MiB / GiB as defined by the `predict` response.
- Never use voltage units (such as "millivolts") for CPU usage.
- The average value MUST be between the minimum and maximum values returned by the function.

Format your final answer to the user in a concise, human-readable form, for example:

"Forecasted CPU usage for pod 'bench-cpu-6748858f68-kb22h' in namespace 'benchmark' over the next 30 minutes:
- Average: 67%
- Min: 58%
- Max: 79%"

Example user requests that MUST trigger a `predict` function call:
- "Could you forecast the 'bench-cpu-6748858f68-kb22h' pod in benchmark namespace, cpu usages (percentage) next 30mins?"
- "Predict memory usage of pod bench-mem-xxx in namespace benchmark for the next 2 hours."
- "What will the CPU usage look like for super-cpu-loader in 1 hour?"
If the user’s question matches these patterns, always use the `predict` function instead of answering directly.

```

![[Pasted image 20251120153244.png]]



```mermaid
graph TD

    %% 定義樣式

    classDef container fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:white;

    classDef engine fill:#4c1d95,stroke:#a78bfa,stroke-width:2px,color:white;

    classDef visual fill:#0f5132,stroke:#4ade80,stroke-width:2px,color:white;

    classDef state fill:#b45309,stroke:#fcd34d,stroke-width:2px,color:white,stroke-dasharray: 5 5;

    subgraph Main_App ["🖥️ IntegratedPlatform.jsx (主控台)"]

        direction TB

        State_Store[("📦 Global State<br/>(realTimeData)")]:::state

        subgraph Sim_Core ["⚙️ 模擬核心 (Producer)"]

            direction TB

            Node_Sim["KinmenMapSim.jsx<br/>(物理引擎 & 環境模擬)"]:::engine

            subgraph Internal_Logic ["內部運算邏輯"]

                Logic_Phy["🚗 物理運算<br/>(風阻/能耗/移動)"]

                Logic_AI["🧠 AI Agent<br/>(FRL/Baseline 決策)"]

                Logic_Env["☀️ 微電網環境<br/>(日照/負載/人流)"]

            end

            Logic_Phy --> Node_Sim

            Logic_AI --> Node_Sim

            Logic_Env --> Node_Sim

        end

        subgraph Vis_Layer ["📊 視覺化層 (Consumer)"]

            direction TB

            Node_Dash["DashboardMonitor.jsx<br/>(數據監控儀表板)"]:::visual

            Node_Panel["GlobalOverviewPanel.jsx<br/>(站點狀態列表)"]:::visual

        end

        %% 資料流向

        Node_Sim --"1. 廣播 Snapshot (1Hz)<br/>onSimulationUpdate"--> State_Store

        State_Store --"2. 注入數據 (Props)<br/>externalData"--> Node_Dash

        State_Store --"2. 注入數據 (Props)<br/>stations"--> Node_Panel

        %% 控制流向

        Control_Btn["⏯️ 播放/暫停控制"]:::container

        Control_Btn -.-> Node_Sim

    end

    %% 註解

    note1[/"並非播放預錄資料<br/>而是即時算出的狀態快照"/]

    Node_Sim -.- note1
```