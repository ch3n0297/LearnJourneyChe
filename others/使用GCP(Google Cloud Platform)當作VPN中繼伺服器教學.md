# 一、在 GCP 架設 WireGuard 伺服器

## 1. 建立 GCP VM

1. **建立 VM**
    
    - 在 Google Cloud Console 建立一台 Compute Engine VM（建議使用 Debian / Ubuntu 等常見發行版）。
    - 指派或保留一個「靜態外部 IP」，方便日後連線固定不變。
    - 進入 VM 後，透過 SSH 連線到該系統 (可用瀏覽器內建的 SSH，或用 gcloud CLI 等方式)。
2. **開放 GCP 防火牆**
    
    - 進入「VPC network」>「Firewall」(或「Firewall rules」)。
    - 建立新的防火牆規則，允許 UDP 51820 埠（WireGuard 預設）：
        - **Name**: `allow-wireguard-udp51820`
        - **Direction**: Ingress
        - **Action**: Allow
        - **Targets**: All instances in the network（或指定 VM Tag）
        - **Source IP ranges**: `0.0.0.0/0`（視需求而定）
        - **Protocols and ports**: `udp:51820`

> **若找不到「VPC network」或「Firewall」**
> 
> - 確認你的帳號/專案有啟用 Compute Engine API 並具備足夠權限 (Editor 或 Owner)。
> - 也可以用 GCP 頂部搜尋關鍵字「Firewall rules」。

---

## 2. 在 VM 上安裝 WireGuard

### (a) 安裝套件

以 Debian/Ubuntu 為例：

bash

複製程式碼

`sudo apt update sudo apt install wireguard`

若是舊版系統，可能要安裝 `wireguard-tools`、`wireguard-dkms` 等。安裝完成後，系統應具有 `wg`、`wg-quick` 等指令可用。

### (b) 建立金鑰

bash

複製程式碼

`cd /etc/wireguard sudo wg genkey | tee server_private.key | wg pubkey > server_public.key`

- `server_private.key`：伺服器私鑰
- `server_public.key`：伺服器公鑰

查看金鑰：

bash

複製程式碼

`sudo cat server_private.key sudo cat server_public.key`

應該是 Base64 編碼的字串，不要用 `< >` 角括號做為占位符。

---

## 3. 建立 WireGuard 組態檔 `wg0.conf`

在 `/etc/wireguard/` 底下，建立並編輯 `wg0.conf`：

bash

複製程式碼

`sudo nano /etc/wireguard/wg0.conf`

範例內容：

ini

複製程式碼

`[Interface] Address = 10.8.0.1/24 ListenPort = 51820 PrivateKey = <server_private_key>  # 貼上真正的 Base64 字串，不要含括號 SaveConfig = false                 # 如果要手動編輯Peer，建議關掉true PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT`

- `Address = 10.8.0.1/24`：VPN 虛擬介面 IP
- `ListenPort = 51820`：監聽埠
- `PrivateKey`：伺服器私鑰字串（請完整貼上，例如 `jZ7Z5dF1GxJ9uFRWh/5OEusMO3m62PcZ/KmfiB3s4GE=`），**不要**再寫 `<server_private_key>`。
- `SaveConfig`：若設 `true`，每次停止服務會用「runtime 狀態」覆寫檔案；可能導致手動編輯的 Peer 被洗掉，建議關掉 (移除或改成 false)。

---

## 4. 啟動 WireGuard

1. **啟動服務**
    
    bash
    
    複製程式碼
    
    `sudo systemctl enable wg-quick@wg0 sudo systemctl start wg-quick@wg0`
    
    或用：
    
    bash
    
    複製程式碼
    
    `sudo wg-quick up /etc/wireguard/wg0.conf`
    
    若有錯誤，可用 `sudo systemctl status wg-quick@wg0` 或 `journalctl -u wg-quick@wg0` 來檢查。
    
2. **若出現「Key is not the correct length or format」**
    
    - 常見原因：把 `<server_private_key>` 字面符號放進組態檔，或貼錯金鑰（包含多餘空白、換行等）。
    - 解法：貼上真正的 Base64 字串，確認無多餘字元或空格。
3. **確認介面**
    
    - 啟動後，執行 `ip addr` 或 `wg`，可看到 `wg0` 介面與伺服器端的公私鑰。

---

# 二、常見問題 & 解法

## 1. Peer 設定被洗掉

- 若在 `[Interface]` 裡設定 `SaveConfig = true`，然後手動編輯了 `[Peer]`，重啟後可能會被 runtime 狀態覆蓋。
- 解法：將 `SaveConfig = true` 移除或改成 false，重啟後就不會覆蓋手動設定。

## 2. Key 不正確長度格式

- 表示 `PrivateKey = ...` 或 `PublicKey = ...` 的字串有誤：多了括號、換行、不完整、無結尾 `=` 等。
- 解法：重新產生並貼上真實 Base64。長度多為 44 位 (或結尾 `=`)。

## 3. 防火牆、NAT 問題

- 確認 GCP VPC 已開放埠 51820/UDP。
- 若系統內建防火牆 (iptables, ufw) 存在阻擋，也需放行對應埠號與介面。

---

# 三、加入多個 Peer（Windows、macOS 客戶端）

## 1. 伺服器端：`wg0.conf` 新增多個 `[Peer]`

假設已有一個 Windows 和一個 macOS，需要各給一個 IP (如 `10.8.0.2`、`10.8.0.3`)。
```ini title:wg0.conf
[Interface] Address = 10.8.0.1/24 
ListenPort = 51820 
PrivateKey = <server_private_key> 
###為了在每次重新啟動中繼伺服器的conf檔案保持一致。
SaveConfig = false

### Peer 1 (Windows) 
[Peer] PublicKey = <windows_public_key> 
AllowedIPs = 10.8.0.2/32

### Peer 2 (macOS) 
[Peer] PublicKey = <mac_public_key> 
AllowedIPs = 10.8.0.3/3
```

- 每個 Peer 都要有獨立的 `[Peer]` 區塊，並使用其「客戶端的公鑰 (`PublicKey`)」和對應的 IP。
- `AllowedIPs = x.x.x.x/32` 表示當封包的目的 IP 是 `x.x.x.x`，就路由給該 Peer。

## 2. Windows 客戶端

1. **安裝 WireGuard**
    - 從 WireGuard 官網 或 Microsoft Store 安裝。
2. **建立隧道**
    - 可在 GUI 裡 `Add Tunnel` -> `Add empty tunnel`，產生 Windows 端公私鑰。
    - 貼上伺服器公鑰、設定 `Endpoint = <伺服器IP>:51820`、`Address = 10.8.0.2/24` 等。
3. **啟動**
    - 雙擊該虛擬伺服器或點「Activate」啟動後，測試 `ping 10.8.0.1` 看能否通。

## 3. macOS 客戶端

1. **安裝 WireGuard for macOS**
    - 從 [App Store](https://apps.apple.com/app/wireguard/id1451685025) 或 官方網站 下載。
2. **產生公私鑰**
    - 在 App 內點「`+` > Create from scratch」，它會生成 `[Interface]` 裡的 `PrivateKey` 與 `PublicKey`。
3. **填入伺服器資訊**
    - `[Peer]` 裡填 `PublicKey = <server_public_key>`，`Endpoint = <伺服器IP>:51820`，`AllowedIPs` 視需求設 `0.0.0.0/0` 或 `10.8.0.0/24`。
    - `[Interface]` 裡 `Address = 10.8.0.3/24`，`PrivateKey = <mac_private_key>`。
4. **伺服器端新增 Peer 2**
    - 在 `wg0.conf` 裡 `[Peer]` 區塊填上 macOS 的 `PublicKey = ...`，以及 `AllowedIPs = 10.8.0.3/32`。
5. **啟動後測試**
    - `ping 10.8.0.1` (伺服器端 IP)。伺服器也可 `ping 10.8.0.3`。

---

# 四、SMB 共享資料夾的應用 (選擇性)

若你的目標是「讓客戶端透過 WireGuard VPN 存取家用/公司的 Windows 共享資料夾 (SMB)」：

1. **確保 Windows 共享已啟用**
    - 右鍵資料夾 > 屬性 > 進階共用 (Advanced Sharing)。
    - Windows 防火牆允許「檔案和印表機共用」在私有網路通過。
2. **VPN 上的 IP**
    - 例如你的共享電腦 IP 為 `10.8.0.2`，客戶端可用 `\\10.8.0.2\share` 方式連線。
3. **確保系統防火牆未擋 SMB**
    - 在 WireGuard VPN 介面上(視為 private/內部網路)允許 SMB 流量 (埠 445 / TCP) 或使用者/密碼驗證。

---

# 五、總結 & 排錯步驟

1. **先確認 GCP 防火牆、系統防火牆都已開放 `UDP 51820`**。
2. **`wg0.conf` 的 `PrivateKey` 務必是正確的 Base64 字串**，不要保留教學範例中的 `< >`。
3. **如果 Peer 消失**：把 `SaveConfig = true` 移除或改成 false，才不會在重啟時自動覆蓋檔案。
4. **多個客戶端**：每個用戶要一組公私鑰、在伺服器端有對應的 `[Peer]` 區塊，並使用不同的 `AllowedIPs` (各佔一個 /32 IP)。
5. **macOS/Windows 連線失敗**：
    - 檢查 IP 是否衝突、金鑰有沒有貼錯。
    - 檢查是否能 `ping` 通伺服器或用 `sudo wg` 看 Peer 是否有「handshake」。
    - 如果 ping 不通，可能是防火牆或路由設定問題。
6. **SMB 應該只在 VPN 內部開放**，千萬不要直接把 445 埠開到公網。

---

## 參考與提醒

- [WireGuard 官方網站](https://www.wireguard.com/) 有更詳細的官方文件與教學。
- 每當你在系統上遇到 WireGuard 無法啟動或連線失敗，可以透過：
    - `sudo systemctl status wg-quick@wg0`
    - `journalctl -u wg-quick@wg0`
    - `sudo wg` (查看 Peer 連線狀態)  
        來進行排查。

---

### 最後結論

- 只要正確設定 GCP 防火牆、貼上正確的私鑰格式，並讓各客戶端 (Windows、macOS) 各有自己的 Peer 區塊，一般就能順利在 WireGuard VPN 上互通。
- 若發生 Key 格式錯誤、Peer 被洗掉等狀況，依照上文檢查並關閉 `SaveConfig`、手動重新填寫正確金鑰即可。
