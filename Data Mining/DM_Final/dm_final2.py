
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import os

# 建立儲存結果的資料夾
results_dir = "results_project2"
os.makedirs(results_dir, exist_ok=True)

# 1. 載入資料
try:
    df = pd.read_csv("content/Mall_Customers.csv")
except FileNotFoundError:
    print("錯誤：找不到 'content/Mall_Customers.csv'。請確保檔案路徑正確。")
    exit()

print("--- 原始資料概覽 ---")
print(df.head())
print("\\n--- 原始資料資訊 ---")
df.info()
print("\\n--- 原始資料描述性統計 ---")
print(df.describe())
print("\\n--- 檢查缺失值 ---")
print(df.isnull().sum())

# 2. 資料探索與預處理
# CustomerID 通常不參與聚類分析，但可以先保留，最後不選入特徵集
# 編碼 Gender
le = LabelEncoder()
df['Gender'] = le.fit_transform(df['Gender']) # Female: 0, Male: 1

# 選取用於聚類的特徵
# 我們主要關注 Age, Annual Income, Spending Score, 和 Gender
features = ['Age', 'Annual Income (k$)', 'Spending Score (1-100)', 'Gender']
X = df[features].copy()

# 標準化數值特徵
scaler = StandardScaler()
X[['Age', 'Annual Income (k$)', 'Spending Score (1-100)']] = scaler.fit_transform(X[['Age', 'Annual Income (k$)', 'Spending Score (1-100)']])

print("\\n--- 預處理後的資料 (前5筆) ---")
print(X.head())

# 3. 數據探索與視覺化
print("\\n--- 進行數據探索與視覺化 ---")
# Pairplot 觀察特徵間關係與分佈
plt.figure(figsize=(12, 8))
sns.pairplot(df[['Age', 'Annual Income (k$)', 'Spending Score (1-100)', 'Gender']], hue='Gender', diag_kind='kde')
plt.suptitle('Pairplot of Features', y=1.02)
pairplot_path = os.path.join(results_dir, "pairplot.png")
plt.savefig(pairplot_path)
print(f"Pairplot 已儲存至: {pairplot_path}")
plt.close()

# 觀察 Annual Income 和 Spending Score 的關係
plt.figure(figsize=(10, 6))
sns.scatterplot(x='Annual Income (k$)', y='Spending Score (1-100)', data=df, hue='Gender')
plt.title('Annual Income vs. Spending Score')
income_spending_scatter_path = os.path.join(results_dir, "income_vs_spending_scatter.png")
plt.savefig(income_spending_scatter_path)
print(f"Income vs Spending scatter plot 已儲存至: {income_spending_scatter_path}")
plt.close()

# 4. 模型建立與聚類結果
# K-Means 聚類實作，並用 Elbow Method 決定最佳群數
# 為了視覺化方便，我們先用 'Annual Income (k$)' 和 'Spending Score (1-100)' 這兩個主要特徵進行聚類和視覺化
X_subset = X[['Annual Income (k$)', 'Spending Score (1-100)']].copy() # 使用標準化後的數據

sse = []
k_range = range(1, 11)
for k in k_range:
    kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42, n_init='auto')
    kmeans.fit(X_subset)
    sse.append(kmeans.inertia_)

# 繪製 Elbow Method 圖
plt.figure(figsize=(10, 6))
plt.plot(k_range, sse, marker='o')
plt.title('Elbow Method for Optimal k (Income vs Spending)')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Sum of Squared Distances (SSE)')
elbow_path = os.path.join(results_dir, "elbow_method_income_spending.png")
plt.savefig(elbow_path)
print(f"Elbow method plot 已儲存至: {elbow_path}")
plt.close()

# 根據 Elbow Method，假設 k=5 是最佳群數 (常見的選擇)
optimal_k = 5
kmeans = KMeans(n_clusters=optimal_k, init='k-means++', random_state=42, n_init='auto')
df['Cluster_Income_Spending'] = kmeans.fit_predict(X_subset)

# 視覺化聚類結果 (Annual Income vs Spending Score)
plt.figure(figsize=(12, 8))
sns.scatterplot(x=X_subset['Annual Income (k$)'], y=X_subset['Spending Score (1-100)'], hue=df['Cluster_Income_Spending'], palette=sns.color_palette("hsv", optimal_k), s=100, alpha=0.7, edgecolor='k')
plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=300, c='red', marker='X', label='Centroids')
plt.title(f'Customer Segments (k={optimal_k}) based on Income and Spending Score (Standardized Data)')
plt.xlabel('Annual Income (k$) (Standardized)')
plt.ylabel('Spending Score (1-100) (Standardized)')
plt.legend()
clusters_income_spending_path = os.path.join(results_dir, "clusters_income_spending.png")
plt.savefig(clusters_income_spending_path)
print(f"Clusters (Income vs Spending) plot 已儲存至: {clusters_income_spending_path}")
plt.close()

# 現在考慮所有選定特徵 (Age, Annual Income, Spending Score, Gender) 進行聚類
sse_all_features = []
for k in k_range:
    kmeans_all = KMeans(n_clusters=k, init='k-means++', random_state=42, n_init='auto')
    kmeans_all.fit(X) # 使用包含所有標準化特徵的 X
    sse_all_features.append(kmeans_all.inertia_)

# 繪製 Elbow Method 圖 (所有特徵)
plt.figure(figsize=(10, 6))
plt.plot(k_range, sse_all_features, marker='o')
plt.title('Elbow Method for Optimal k (All Features)')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Sum of Squared Distances (SSE)')
elbow_all_features_path = os.path.join(results_dir, "elbow_method_all_features.png")
plt.savefig(elbow_all_features_path)
print(f"Elbow method plot (all features) 已儲存至: {elbow_all_features_path}")
plt.close()

# 假設根據 Elbow Method (所有特徵)，k=6 是較好的選擇 (或根據實際圖形判斷)
optimal_k_all_features = 6 # 這裡假設為6，實際應根據圖形判斷
kmeans_all_features = KMeans(n_clusters=optimal_k_all_features, init='k-means++', random_state=42, n_init='auto')
df['Cluster_All_Features'] = kmeans_all_features.fit_predict(X)

# 利用 PCA 將高維特徵降維至 2D，繪製聚類視覺化圖
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X)
df_pca = pd.DataFrame(data=X_pca, columns=['PCA1', 'PCA2'])
df_pca['Cluster'] = df['Cluster_All_Features']

plt.figure(figsize=(12, 8))
sns.scatterplot(x='PCA1', y='PCA2', hue='Cluster', data=df_pca, palette=sns.color_palette("hsv", optimal_k_all_features), s=100, alpha=0.7, edgecolor='k')
# 計算 PCA 轉換後的中心點
centroids_pca = pca.transform(kmeans_all_features.cluster_centers_)
plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], s=300, c='red', marker='X', label='Centroids (PCA)')
plt.title(f'Customer Segments (k={optimal_k_all_features}) using PCA (All Features)')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.legend()
clusters_pca_path = os.path.join(results_dir, "clusters_pca_all_features.png")
plt.savefig(clusters_pca_path)
print(f"Clusters (PCA, all features) plot 已儲存至: {clusters_pca_path}")
plt.close()

print("\\n--- 聚類分析完成 ---")
# 5. 聚類分析與商業洞察 (這部分主要在報告中撰寫)
# 可以輸出每個群集的描述性統計
print(f"\\n--- 描述性統計 (基於 {optimal_k_all_features} 個群集, 使用所有特徵) ---")
# 將原始未標準化的數據與群集標籤合併，以便解釋
# 為了簡化，我們直接使用原始 df 的數據 (CustomerID, Age, Annual Income (k$), Spending Score (1-100))，並加入 Cluster_All_Features 和轉換回來的 Gender
df_analysis = df[['CustomerID', 'Age', 'Annual Income (k$)', 'Spending Score (1-100)']].copy()
df_analysis['Gender'] = le.inverse_transform(df['Gender']) # 將 Gender 從數字轉回 Female/Male
df_analysis['Cluster'] = df['Cluster_All_Features']


cluster_summary = df_analysis.groupby('Cluster').agg(
    Count=('CustomerID', 'count'),
    Avg_Age=('Age', 'mean'),
    Median_Age=('Age', 'median'),
    Avg_Annual_Income=('Annual Income (k$)', 'mean'),
    Median_Annual_Income=('Annual Income (k$)', 'median'),
    Avg_Spending_Score=('Spending Score (1-100)', 'mean'),
    Median_Spending_Score=('Spending Score (1-100)', 'median'),
    Mode_Gender=('Gender', lambda x: x.mode()[0] if not x.mode().empty else 'N/A') # 處理空 Series 的情況
).round(2)

print(cluster_summary)
cluster_summary_path = os.path.join(results_dir, "cluster_summary_all_features.csv")
cluster_summary.to_csv(cluster_summary_path)
print(f"Cluster summary 已儲存至: {cluster_summary_path}")

print("\\n--- dm_final2.py 執行完畢 ---")
