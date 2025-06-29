
![[Pasted image 20250520215407.png | 600]]
### IPsec 測驗一問一答

1. **IPsec 的主要目的是什麼？**
    
    - IPsec 的主要目的是在 IP 層提供安全服務，如驗證、機密性和金鑰管理，保護跨網路傳輸的資料流量。
	    
	    
2. **除了單一協定，IPsec 是由什麼組成的？**
    
    - IPsec 是一套安全演算法與一個通用框架，允許通訊雙方選擇適合的安全機制來保障資料傳輸。
	    
	    
3. **請列出 IPsec 的兩種安全標頭延伸。**
    
    - 驗證標頭（AH）與封裝安全酬載（ESP）是 IPsec 的兩種安全標頭延伸。
        
        
4. **什麼是安全關聯 (Security Association, SA)？**
    
    - 安全關聯是一種單向的邏輯關係，用來定義如何套用安全服務來保護 IP 資料流。
        
        
5. **安全關聯 (SA) 如何定義？**
    
    - 一個 SA 是由三個主要參數定義：安全參數索引 (SPI)、IP 目的地地址、與安全協定識別碼。
        
        
6. **驗證標頭 (Authentication Header, AH) 提供哪些安全服務？**
    
    - AH 提供資料完整性與資料來源驗證，使用 MAC（如 HMAC-MD5 或 HMAC-SHA-1）防止訊息被竄改。
        
        
7. **封裝安全酬載 (Encapsulating Security Payload, ESP) 提供哪些安全服務？**
    
    - ESP 提供資料加密（機密性），並可選擇性提供資料完整性與身份驗證服務。
        
        
8. **IPsec 的傳輸模式與通道模式有何不同？**
    
    - 傳輸模式只加密 IP 酬載；通道模式則加密整個 IP 封包並加入新的 IP 標頭。傳輸模式常用於端對端通訊，通道模式則用於 VPN 等網關對網關通訊。
        
        
9. **IPsec 中的金鑰管理涵蓋哪些方面？**
    
    - 涵蓋金鑰的產生、分發與管理，可手動設定或使用自動化的協定來完成。
        
        
10. **Oakley 和 ISAKMP 在 IPsec 金鑰管理中扮演什麼角色？**
    
    - Oakley 是一種改良的 Diffie-Hellman 金鑰交換協定，而 ISAKMP 是一個通用框架，用於建立、協商與管理安全關聯，並可結合 Oakley 進行實際的金鑰交換。
      
      