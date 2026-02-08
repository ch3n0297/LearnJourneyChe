## 0. 起點：行進正弦波

$$
y(x,t)=y_m\sin(kx-\omega t)  
$$ 
且  
$$
k=\frac{2\pi}{\lambda},\quad \omega=\frac{2\pi}{T_{\text{period}}}  
$$
（這裡我用 (T_{\text{period}}) 代表「週期」，避免跟張力 (T) 混淆。）

波速（波形前進速度）：  
$$ 
v=\frac{\omega}{k}=\frac{\lambda}{T_{\text{period}}}  
$$

---

## 1. 固定位置 (x) 的上下速度
$$
u(x,t)=\left.\frac{\partial y}{\partial t}\right|_x  
=-\omega y_m\cos(kx-\omega t)  $$

---

## 2. 一小段繩子 (dx) 的動能

線密度 (\mu)（kg/m），所以 (dm=\mu dx)：  
$$
dK=\frac12,dm,u^2  
=\frac12(\mu dx),\omega^2y_m^2\cos^2(kx-\omega t)  
$$

---

## 3. 一個波長 (\lambda) 內的總動能 (\Delta K)

$$  
\Delta K=\int_0^{\lambda} dK  
=\frac12\mu\omega^2y_m^2\int_0^{\lambda}\cos^2(\cdot),dx  
$$
而 (\cos^2) 在一個週期的平均值是 (1/2)，所以  
$$
\int_0^{\lambda}\cos^2(\cdot),dx=\frac{\lambda}{2}  $$  
得到  
$$  
\Delta K=\frac14,\mu,\omega^2y_m^2,\lambda  
$$

---

## 4. 平均動能傳遞率（動能功率）

每個週期 (T_{\text{period}}) 波形前進一個波長 (\lambda)，所以  
$$
\overline{\frac{dK}{dt}}=\frac{\Delta K}{T_{\text{period}}}  
=\frac14\mu\omega^2y_m^2\frac{\lambda}{T_{\text{period}}}  
=\frac14\mu\omega^2y_m^2,v  
$$

---

## 5. 位能平均同樣大小，因此總平均功率

對正弦行進波，張力位能與斜率平方相關，平均後會得到：  
$$
\overline{\frac{dU}{dt}}=\overline{\frac{dK}{dt}}  
$$ 
所以總能量平均傳遞率（平均功率）：  
$$  
\overline{\frac{dE}{dt}}  
=\overline{\frac{dK}{dt}}+\overline{\frac{dU}{dt}}  
=2\overline{\frac{dK}{dt}}  
=\frac12,\mu,\omega^2y_m^2,v  
$$ 
這就是你板書最後那行。

---

# 6. 把繩波波速 (v=\sqrt{T/\mu}) 代進去（你要加的部分）

對繩波（張力 (T)，線密度 (\mu)）波速是：  
$$ 
v=\sqrt{\frac{T}{\mu}}  
$$

代回總平均功率：  
$$
\boxed{  
\overline{\frac{dE}{dt}}  
=\frac12,\mu,\omega^2y_m^2,\sqrt{\frac{T}{\mu}}  
}
$$

常見也會整理成更乾淨的形式：  
$$
\boxed{  
\overline{\frac{dE}{dt}}  
=\frac12,\omega^2y_m^2,\sqrt{T\mu}  
}  
$$
因為  
$$ 
\mu\sqrt{\frac{T}{\mu}}=\sqrt{T\mu}  
$$

---

## 最終你可以背的三個盒裝結論

1. 波速（繩波）：  
    $$  
    \boxed{v=\sqrt{\frac{T}{\mu}}}  
    $$
    
2. 平均功率（能量傳遞率）：  
    $$  
    \boxed{\overline{P}=\overline{\frac{dE}{dt}}=\frac12,\mu,\omega^2y_m^2,v}  
    $$
    
3. 代入繩波波速後：  
    $$ 
    \boxed{\overline{P}=\frac12,\omega^2y_m^2,\sqrt{T\mu}}  
    $$


### 題目清單（波）

#### W-001

- **來源**：題本截圖（題號 13）
    
- **主題標籤**：行波疊加 / 駐波 / 腹點（antinodes）/ 最大位移
    
- **題目內容**：
    
    - Two transverse sinusoidal waves combining in a medium are described by the wave functions
        
        y1=3.00sin⁡(π(x+0.600t)),y2=3.00sin⁡(π(x−0.600t))y_1 = 3.00\sin\big(\pi(x+0.600t)\big),\quad y_2 = 3.00\sin\big(\pi(x-0.600t)\big)y1​=3.00sin(π(x+0.600t)),y2​=3.00sin(π(x−0.600t))
        
        where xxx, y1y_1y1​, and y2y_2y2​ are in centimeters and ttt is in seconds.
        
    - Determine the maximum transverse position of an element of the medium at  
        (a) x=0.250 cmx = 0.250\ \text{cm}x=0.250 cm,  
        (b) x=0.500 cmx = 0.500\ \text{cm}x=0.500 cm, and  
        (c) x=1.50 cmx = 1.50\ \text{cm}x=1.50 cm.
        
    - (d) Find the three smallest values of xxx corresponding to antinodes.
        
- **附圖**：無
    
- **備註**：—
    

---

#### W-002

- **來源**：題本截圖（題號 8，Figure P14.8）
    
- **主題標籤**：聲波干涉 / 強度極大極小 / 雙聲源 / 幾何路徑差
    
- **題目內容**：
    
    - Why is the following situation impossible?
        
    - Two identical loudspeakers are driven by the same oscillator at frequency 200 Hz200\ \text{Hz}200 Hz.
        
    - They are located on the ground a distance d=4.00 md = 4.00\ \text{m}d=4.00 m from each other.
        
    - Starting far from the speakers, a man walks straight toward the right-hand speaker as shown in Figure P14.8.
        
    - After passing through three minima in sound intensity, he walks to the next maximum and stops.
        
    - Ignore any sound reflection from the ground.
        
- **附圖**：有（Figure P14.8；兩喇叭間距 ddd，人到右喇叭的直線距離標成 xxx）
    
- **備註**：—
    

---

#### W-003

- **來源**：題本截圖（題號 7）
    
- **主題標籤**：脈衝波 / 行進方向判斷 / 疊加與相消
    
- **題目內容**：
    
    - Two pulses traveling on the same string are described by
        
        y1=5(3x−4t)2+2,y2=−5(3x+4t−6)2+2y_1=\frac{5}{(3x-4t)^2+2},\quad y_2=\frac{-5}{(3x+4t-6)^2+2}y1​=(3x−4t)2+25​,y2​=(3x+4t−6)2+2−5​
    - (a) In which direction does each pulse travel?
        
    - (b) At what instant do the two cancel everywhere?
        
    - (c) At what point do the two pulses always cancel?
        
- **附圖**：無
    
- **備註**：—
    

---

#### W-004

- **來源**：題本截圖（題號 3）
    
- **主題標籤**：相位差 / 兩波疊加 / 干涉條件
    
- **題目內容**：
    
    - Two sinusoidal waves in a string are defined by the wave functions
        
        y1=2.00sin⁡(20.0x−32.0t),y2=2.00sin⁡(25.0x−40.0t)y_1 = 2.00\sin(20.0x-32.0t),\quad y_2 = 2.00\sin(25.0x-40.0t)y1​=2.00sin(20.0x−32.0t),y2​=2.00sin(25.0x−40.0t)
        
        where xxx, y1y_1y1​, and y2y_2y2​ are in centimeters and ttt is in seconds.
        
    - (a) What is the phase difference between these two waves at the point x=5.00 cmx=5.00\ \text{cm}x=5.00 cm at t=2.00 st=2.00\ \text{s}t=2.00 s?
        
    - (b) What is the positive xxx value closest to the origin for which the two phases differ by ±π\pm\pi±π at t=2.00 st=2.00\ \text{s}t=2.00 s? (At that location, the two waves add to zero.)
        
- **附圖**：無
    
- **備註**：—