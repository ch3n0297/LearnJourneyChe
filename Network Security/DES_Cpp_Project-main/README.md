# DES 加密/解密專案

這是一個實作 DES (Data Encryption Standard) 加密演算法的 C++ 專案，支援多種操作模式並提供 GUI 介面。

## 功能特色

- **DES 演算法實作**：完整的 DES 加密/解密功能
- **多種操作模式**：
  - ECB (Electronic Codebook)
  - CFB (Cipher Feedback)
  - CTR (Counter)
- **GUI 介面**：使用 ImGui 提供直觀的圖形化操作介面
- **檔案操作**：支援檔案的加密和解密

## 專案結構

```
C-project/
├── include/           # 頭文件
├── src/               # 源代碼
├── test/              # 測試檔案
├── build/             # 編譯輸出
├── third_party/       # 第三方庫
├── scripts/           # 打包腳本 (Linux/macOS/Windows)
├── dist/              # 產生的安裝包
├── docs/              # 操作文檔
└── Makefile           # 跨平台建置設定
```

## 編譯、執行與打包

本專案以跨平台 **Makefile** 管理建置流程；下載後無論在 **Linux / macOS / Windows** 皆可直接使用 `make` 指令完成編譯、執行與打包。

> **預先需求**  
> - C++17 相容編譯器（GCC 10+/Clang 13+/MSVC 2022）  
> - OpenGL 與 GLFW (macOS 可用 `brew install glfw`; Ubuntu/Debian 請 `sudo apt install libglfw3-dev libgl1-mesa-dev`)  
> - （可選）`tree`、`zip`、`hdiutil`、`appimagetool`…等工具已由腳本自動處理

| 常用目標 | 功能 | 備註 |
|----------|------|------|
| `make` 或 `make help` | 顯示指令一覽 | 預設目標 |
| `make all`           | 僅編譯可執行檔 | 位於 `build/des_gui_app` |
| `make run`           | **編譯（若必要）並立即執行** | 最方便的快速測試 |
| `make package`       | 依偵測到的 OS 產生可攜發佈包 | <br>• **Windows:** `dist/des_gui-win64.zip`<br>• **macOS:** `dist/DES_GUI.app` 或 `dist/des_gui-mac.dmg`<br>• **Linux:** `dist/des_gui-linux.AppImage` |
| `make clean`         | 移除 `build/` 及其他暫存檔 | 重新編譯前可先清理 |

### 範例：首次下載執行

```bash
# 1. 取得原始碼後
git clone <repo-url> && cd C-project

# 2. 一鍵編譯＋執行
make run
```

### 範例：建立可攜安裝包（Packaging）

```bash
# 產生對應平台安裝包／可攜包
make package

# 輸出位置：
#   dist/des_gui-win64.zip          (Windows)
#   dist/DES_GUI.app  或 .dmg       (macOS)
#   dist/des_gui-linux.AppImage     (Linux)
```

## 使用說明

1. 啟動程式後會出現 GUI 介面
2. 選擇要執行的 DES 模式 (ECB/CFB/CTR)
3. 輸入金鑰和初始向量 (若需要)
4. 選擇輸入檔案
5. 執行加密或解密操作

## 作者

黃教丞 (第2組)
日期: 2025/05/23
