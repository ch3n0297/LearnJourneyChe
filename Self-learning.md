# 自學報告：Markdown 基本語法快速學習與範例

## 學習目標
本次自學目標為：  
- 掌握 Markdown 基本語法，包括標題、粗體、斜體、列表、程式碼區塊、圖片插入與表格。  
- 透過實際範例，了解如何在 VS Code/Typora/Obsidian 中撰寫易讀、易維護的技術文檔。

## 學習過程
1. **教學資源**  
   - 參考線上教學（快速瀏覽標題、文字格式、列表、程式碼區塊、圖片與表格語法）。  
   - 確認常用連結：[Markdown 指南](https://www.markdownguide.org/basic-syntax)（僅供參考）。  

1. **建立與編輯 `.md` 檔**  
   - 在 VS Code 或 Obsidian 中新建 `markdown_sample.md`。  
   - 依照以下範例，依序嘗試各種元素：  
     1. **標題**：使用 `#` 到 `######` 共六級標題。  
     2. **文字格式**：  
        - 粗體：`**粗體文字**` → **粗體文字**  
        - 斜體：`*斜體文字*` → *斜體文字*  
     3. **列表**：  
        - 無序列表：使用 `-` 或 `*`。  
        - 有序列表：使用 `1.`, `2.`, `3.`。  
     4. **程式碼區塊**：  
        ```python
        def hello_markdown():
            print("Hello, Markdown!")
        ```
		在使用程式碼區塊時，可以只使用`text`或是```text```，然後可以是使用 
		```(這裏可以輸入任何語言的名稱，他會轉換成語法高亮) Title: (可以為一個區塊撰寫標題等等)
		
		```

     5. **插入圖片**：`![範例圖片](images/example.png), ![[images/example.png]]`  
     6. **簡單表格**：  

        | 功能 | 語法範例  |
        | --- | --- |
        | 粗體       | `**粗體**`|
        | 斜體       | `*斜體*` |
        | 標題       | `# 標題`  |
        | 程式碼區塊 | <pre>```python … ```</pre>   |

3. **檔案預覽與修正（約 5 分鐘）**  
   - 可以在IDE或其他Markdown編輯器中切換到預覽模式，檢查所有語法是否正確顯示。  
   - 調整圖片路徑與表格對齊，確保閱讀順暢。 

## 拓展 HTML 語法範例
以下示範在 Markdown 中直接嵌入 HTML，以實現更多自訂排版與互動效果。

1. **內聯 HTML 標籤範例**  
   - 自行定義文字顏色與大小：  
     ```html
     <span style="color: red; font-size: 1.2em;">紅色大字範例</span>
     ```  
   - 強制換行或分隔線：  
     ```html
     這是一行文字。<br>
     下一行文字在另一行。<hr>
     ```
   - 示例結果：  
     <span style="color: red; font-size: 1.2em;">紅色大字範例</span><br>
     這是一行文字。<br>
     下一行文字在另一行。<hr>

2. **使用 `<div>` 進行區塊排版**  
```html
   <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
     <strong>內容區塊示範：</strong>這是一個使用 <code>&lt;div&gt;</code> 標籤，並且帶有邊框和內距的區塊範例。
   </div>
```

- 效果：
> <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
- <strong>內容區塊示範：</strong>這是一個使用 <code>&lt;div&gt;</code> 
- </div>

3. **自訂屬性表格（使用 HTML 語法）**
    
    ```html
    <table style="width:100%; border-collapse: collapse;">
      <tr style="background-color: #f2f2f2;">
        <th style="border: 1px solid #ddd; padding: 8px;">欄位</th>
        <th style="border: 1px solid #ddd; padding: 8px;">範例</th>
      </tr>
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">粗體</td>
        <td style="border: 1px solid #ddd; padding: 8px;"><strong>**粗體**</strong></td>
      </tr>
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">斜體</td>
        <td style="border: 1px solid #ddd; padding: 8px;"><em>*斜體*</em></td>
      </tr>
    </table>
    ```
    
	- 效果（示例表格）：
	<table style="width:100%; border-collapse: collapse;">
      <tr style="background-color: #f2f2f2;">
        <th style="border: 1px solid #ddd; padding: 8px;">欄位</th>
        <th style="border: 1px solid #ddd; padding: 8px;">範例</th>
      </tr>
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">粗體</td>
        <td style="border: 1px solid #ddd; padding: 8px;"><strong>**粗體**</strong></td>
      </tr>
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">斜體</td>
        <td style="border: 1px solid #ddd; padding: 8px;"><em>*斜體*</em></td>
      </tr>
    </table>
    
4. **交互式摺疊內容區塊（`<details>` 與 `<summary>`）**
    
    ```html
    <details>
      <summary>點擊展開/收合更多資訊</summary>
      <p>這是隱藏的詳細內容，可以放程式碼示例、說明文字或任何 HTML 元素，例如：<code><strong>加粗文字</strong>、<em>斜體文字</em>。</code></p>
    </details>
    ```
    
    - 效果：
	    <details>
	      <summary>點擊展開/收合更多資訊</summary>
	      <p>這是隱藏的詳細內容，可以放程式碼示例、說明文字或任何 HTML 元素，例如：<code><strong>加粗文字</strong>、<em>斜體文字</em>。</code></p>
	    </details>
5. **嵌入影音或外部內容**
    
    - 使用 `<iframe>` 嵌入 YouTube 影片：
        
        ```html
        <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ"
          title="YouTube video player" frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen></iframe>
        ```
        
        - 效果（示例影片）：
            <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ"
          title="YouTube video player" frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen></iframe>
    - 從外部載入圖片並設定大小：
        
        ```html
        <img src="https://via.placeholder.com/300x200.png?text=示例圖片" alt="示例圖片" width="300" height="200">
        ```
        
        - 效果（示例圖片）：  
            <img src="https://via.placeholder.com/300x200.png?text=示例圖片" alt="示例圖片" width="300" height="200">

## 心得與下步計畫

透過本次短時間練習，對 Markdown 與 HTML 混用語法有更深入了解，能在同一份 `.md` 檔中靈活使用各種標記與排版技巧。未來若有更多時間，計畫：

1. 深入學習 **進階語法**（例如：自動編號列表、內嵌 HTML 表單元素、CSS 樣式表應用）。
    
2. 探討 **Markdown 檔案轉換**，例如使用 Pandoc 將 `.md` 轉為 PDF、HTML、Word 或 PowerPoint。
    
3. 練習在實際專案中使用這些技巧，例如：
    
    - 在 GitHub Pages 上建立自訂樣式的技術部落格。
        
    - 在 Obsidian 中結合自訂 CSS 與插件以強化筆記功能。
        
4. 學習撰寫客製化 **CSS** 並與 Markdown/HTML 結合，進一步提升文件的可視化與美觀度。

## 學習成果
- **標題層級**：成功運用 `#、##、###` 來區分主、次、細節層級。  
- **文字格式**：能靈活運用 `**粗體**` 與 `*斜體*`，在段落中突顯重點。  
- **列表**：完成一段無序列表與有序列表，說明用途與差異：  
  - 無序列表適合條件或項目列點。  
  - 有序列表適合步驟流程或優先順序。  
- **程式碼區塊**：示範 Python 範例，確認高亮語法正常顯示。  
- **圖片插入**：能以 `![替代文字](圖片路徑)` 插入本地或線上圖片。  
- **表格**：完成簡單的二列表格，了解 `| --- | --- |` 的對齊原理。

