# <span style="font-family: cursive;">生物資訊學-第一次作業</span>
## <span style="font-family: cursive">一、前往 $NCBI$ 查詢基因、解釋原由 </span>  
#uuid1
### <span style="font-family: cursive;">尋找基因</span>
<span style="font-family: cursive;">我利用關鍵詞的搜尋法來尋找</span>
```Plaintext
ACTB[Gene Name] AND refseq[Filter] AND biomol_mrna[Properties]
```
#### <span style="font-family: cursive;">並且有確實的找到以下資訊，可以看到在 $Annotation Provider$ 這邊，顯示出該資料是來自 $RefSeq$，而 $NCBI RefSeq$ $(Reference$  $Sequence$  $Database)$ 是美國國家生物技術資訊中心 $(NCBI)$ 維護的一個基因組、轉錄組和蛋白質序列的標準數據庫。它提供了經過整理和標準化的基因組數據，並進行基因註釋，以確保數據的準確性和一致性。</span>
![[Pasted image 20250320022040.png]]
##### 利用 $Ctrl⌃$ $/$ $Cmd⌘$  $+$ $f$ 標注，並標注 $GGTACC$ 序列。
### <span style="font-family: cursive">為什麼要尋找GGTACC序列呢？</span>
##### <span style="font-family: cursive;">因為 $GGTACC$ 是**限制性內切酶** **$KpnI$ 的識別位點。$Kpn$$I$ 是一種來源於 $Klebsiella$ $pneumoniae$（肺炎克雷伯氏菌）的限制酶，會專一性地識別  $GGTACC$ 並在 $GGTAC$ $|$ $C$ 之間進行切割。</span>
##### <span style="font-family: cursive;">那我尋找的類型為：$Pithys$ $albifrons$ $albifrons$ x的 $ACTB$（$β$ - 肌動蛋白）基因。</span>

![[Pasted image 20250319141638.png]]
## <span style="font-family: cursive">二、下載該 $mRNA$ 的 $GenBank$，$import$進 $CLC$ 並進行 $KpnI$限制酶的加入 </span> 
#uuid2
### <span style="font-family: cursive;"><p style=" text-align: center">點擊Send to</p></span>

![[Pasted image 20250320024205.png]]
<p style=" text-align: center; font-size: 50">↓</p>

### <span style="font-family: cursive;"><p style=" text-align: center">點擊Complete Record to</p></span>

![[Pasted image 20250320024223.png]]
<p style=" text-align: center; font-size: 50">↓</p>

### <span style="font-family: cursive;"><p style=" text-align: center">選取GenBank</p></span>

![[Pasted image 20250320024301.png]]

<p style=" text-align: center; font-size: 50">↓</p>

### <span style="font-family: cursive;"><p style=" text-align: center">再來將載入完成的字體 $import$ 至 $CLC$ $Sequence$ $Viewer$ $7$ </p></span>
![[Pasted image 20250320032105.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[截圖 2025-03-20 凌晨3.22.09.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[截圖 2025-03-20 凌晨3.30.26 1.png]]

<p style=" text-align: center; font-size: 50">↓</p>

### <span style="font-family: cursive"><p style=" text-align: center">點擊 $toolbox$ 中的 $Restriction$ $Site$ $Analysis$ </p></span>

![[Pasted image 20250320035340.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[Pasted image 20250320035409.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[Pasted image 20250320035451.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[Pasted image 20250320040649.png]]
##### <span style="font-family: cursive">這是我們的 $KpnI$ 限制酶的位置</span>




## <span style="font-family: cursive">三、下載該 $protein$ 的 $Sequence$ 並將載好的 $GenePept$資料 $import$ 進 $CLC$ </span> 
#uuid3

### <span style="font-family: cursive"><p style=" text-align: center">再來，回到 $NCBI$ 尋找特徵中的 $Protein$_$id$ ，並將他下載下來</p></span>
![[Pasted image 20250320041341.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[Pasted image 20250320041857.png]]

<p style=" text-align: center; font-size: 50">↓</p>

![[Pasted image 20250320041914.png]]

<p style=" text-align: center; font-size: 50">↓</p>

#### <span style="font-family: cursive">做和前面 [[#<span style="font-family cursive">二、下載該 $mRNA$ 的 $GenBank$，$import$進 $CLC$ 並進行 $KpnI$限制酶的加入 </span> | 步驟二 ]] 的 $Import$ 類似 ，$Import$ 後打開右邊的 $Sequence$ $Settings$，點擊 $Annotation$ $Type$，可根據圖片上的步驟實現。</span>

![[截圖 2025-03-20 凌晨4.46.49.png]]

#### <span style="font-family: cursive">以下為結果呈現</span>
![[Pasted image 20250320050414.png]]




<span style="font-size: 8px; transform: rotate(180deg); display: inline-block">© B1128019同學的防偽標記，以免有人抄襲</span>


<div style="width: 100vw; font-size: 10px; text-align: center;">
  <span class="pageNumber"></span> / <span class="totalPages"></span>
</div>
