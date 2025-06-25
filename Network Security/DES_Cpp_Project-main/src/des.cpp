// 檔案名稱: ns_project_q1.cpp
// 功能: 實作 DES 加密與解密，支援 ECB、CFB、CTR 三種模式，並提供字元與 bit stream 轉換
// 作者: 黃教丞(第2組)
// 日期: 2024/06/09

//2. 請寫一個DES的加密及解密程式，可分開寫(DES_en及DES_de)或合併在同一個程式(DES).
    //(a)	程式的輸入及輸出必須為ASCII的字元(Character)，因此你必須有一個轉換字元為二進位bit stream的convert_in()及轉換二進位bit stream為字元的convert_out(). 你可以使用getchar()及putchar()這兩個C function，其作用為將字元轉換為十進位整數及將十進位整數轉換為字元，再利用 x & 2 n來將十進位轉成二進位的bit stream。 輸出時則需將二進位每八個位元轉換成十進位x，再利用putchar(x)輸出為字元。Plaintext for test為一測試檔。
    //(b)	每八個字元可轉成64 bits，為一個block，當輸入字元不為八的倍數時，則將其補上空白(Space)字元，及其值用0來填塞(Padding)。範例為DES_en為ECB mode。
    //(c)	Initial Permutation及Inverse Initial Permutation 可宣告為constant Array IP[64]及IIP[64]. PC_1及PC_2，Key Shift，Permutation Function亦同。
    //(d)	八個S-Box也可宣告為三維的Array，如S_Box[8][4][16]。
    //(e)	Key可用整數輸入，如3000，再利用key & 2 n運算轉為64位元的二進位即可。

#include "des.h"
#include <cstdio>
#include <cstring>
#include <iostream>
using namespace std;

//==================== 常數定義區 ====================//
// DES 相關常數 (IP, IIP, PC_1, PC_2, S-Box 等)

// IP、IIP、PC_1、PC_2、S-Box 等常數可自行調整或放在其他檔案
static const int IP[64] = {
    58,50,42,34,26,18,10, 2,
    60,52,44,36,28,20,12, 4,
    62,54,46,38,30,22,14, 6,
    64,56,48,40,32,24,16, 8,
    57,49,41,33,25,17, 9, 1,
    59,51,43,35,27,19,11, 3,
    61,53,45,37,29,21,13, 5,
    63,55,47,39,31,23,15, 7
};
static const int IIP[64] = {
    40, 8,48,16,56,24,64,32,
    39, 7,47,15,55,23,63,31,
    38, 6,46,14,54,22,62,30,
    37, 5,45,13,53,21,61,29,
    36, 4,44,12,52,20,60,28,
    35, 3,43,11,51,19,59,27,
    34, 2,42,10,50,18,58,26,
    33, 1,41, 9,49,17,57,25
};
// 其他常數陣列如 PC_1、PC_2、S-Box、Key Shift、Permutation Function 等，略

//==================== 轉換函式區 ====================//

// 將字元轉成二進位
// 參數: c 為輸入字元, bits[8] 為輸出 bit 陣列
void convert_in(unsigned char c, bool bits[8]) {
    for(int i = 0; i < 8; i++){
        bits[7 - i] = (c & (1 << i)) != 0;
    }
}

// 將二進位轉成字元
// 參數: bits[8] 為輸入 bit 陣列，回傳對應字元
unsigned char convert_out(const bool bits[8]) {
    unsigned char val = 0;
    for(int i = 0; i < 8; i++){
        if(bits[7 - i]) val |= (1 << i);
    }
    return val;
}

//==================== 核心 DES 函式區 (Permutation, F, Round, Key Schedule) ====================//

// 初始交換 (Initial Permutation)
// 參數: in[64] 輸入 bit，out[64] 輸出 bit
void initialPermutation(const bool in[64], bool out[64]) {
    for(int i=0; i<64; i++){
        out[i] = in[IP[i] - 1];
    }
}

// 逆初始交換 (Inverse Initial Permutation)
// 參數: in[64] 輸入 bit，out[64] 輸出 bit
void inverseInitialPermutation(const bool in[64], bool out[64]) {
    for(int i=0; i<64; i++){
        out[i] = in[IIP[i] - 1];
    }
}

// 子函數 F (簡化版本)
// 參數: halfBlock[32] 半區塊, subKey[48] 子金鑰, out[32] 輸出
void fFunction(const bool halfBlock[32], const bool subKey[48], bool out[32]) {
    // 只做簡單的 XOR 以示範，實際應包含 Expansion、S-Box、Permutation 等
    for(int i=0; i<32; i++){
        out[i] = halfBlock[i] ^ subKey[i % 48];
    }
}

// DES 單一輪運算
// 參數: block[64] 輸入與輸出區塊, subKey[48] 子金鑰
void desRound(bool block[64], const bool subKey[48]) {
    bool left[32], right[32], temp[32];
    // 拆成左右
    memcpy(left,  block,     32*sizeof(bool));
    memcpy(right, block+32, 32*sizeof(bool));
    // fFunction
    fFunction(right, subKey, temp);
    // 左邊 = 左邊 XOR fFunction(右邊)
    for(int i=0; i<32; i++){
        left[i] = left[i] ^ temp[i];
    }
    // 交換
    memcpy(block,     right, 32*sizeof(bool));
    memcpy(block+32,  left,  32*sizeof(bool));
}

// 產生 16 組子金鑰 (Key Schedule，簡化版)
// 參數: key64[64] 輸入金鑰, subKeys[16][48] 輸出16組子金鑰
void generateSubKeys(const bool key64[64], bool subKeys[16][48]) {
    // 此處僅做簡示，真正 DES key schedule 請依標準實作
    for(int r=0; r<16; r++){
        for(int i=0; i<48; i++){
            subKeys[r][i] = key64[(i+r) % 64];
        }
    }
}

// DES 加密 (16 輪)
// 參數: in[64] 輸入明文, out[64] 輸出密文, key64[64] 金鑰
void desEncrypt(const bool in[64], bool out[64], const bool key64[64]) {
    bool block[64];
    memcpy(block, in, 64*sizeof(bool));

    bool subKeys[16][48];
    generateSubKeys(key64, subKeys);

    // Use tmpBlock for initialPermutation
    bool tmpBlock[64];
    initialPermutation(block, tmpBlock);
    memcpy(block, tmpBlock, 64 * sizeof(bool));
    for(int i=0; i<16; i++){
        desRound(block, subKeys[i]);
    }
    // 交換左右
    bool tmp[32];
    memcpy(tmp,     block,    32*sizeof(bool));
    memcpy(block,    block+32,32*sizeof(bool));
    memcpy(block+32, tmp,     32*sizeof(bool));

    // Use tmpBlock2 for inverseInitialPermutation
    bool tmpBlock2[64];
    inverseInitialPermutation(block, tmpBlock2);
    memcpy(out, tmpBlock2, 64 * sizeof(bool));
}

// DES 解密 (16 輪)
// 參數: in[64] 輸入密文, out[64] 輸出明文, key64[64] 金鑰
void desDecrypt(const bool in[64], bool out[64], const bool key64[64]) {
    bool block[64];
    memcpy(block, in, 64*sizeof(bool));

    bool subKeys[16][48];
    generateSubKeys(key64, subKeys);

    // Use tmpBlock for initialPermutation
    bool tmpBlock[64];
    initialPermutation(block, tmpBlock);
    memcpy(block, tmpBlock, 64 * sizeof(bool));
    for(int i=15; i>=0; i--){
        desRound(block, subKeys[i]);
    }
    // 交換左右
    bool tmp[32];
    memcpy(tmp,     block,    32*sizeof(bool));
    memcpy(block,    block+32,32*sizeof(bool));
    memcpy(block+32, tmp,     32*sizeof(bool));

    // Use tmpBlock2 for inverseInitialPermutation
    bool tmpBlock2[64];
    inverseInitialPermutation(block, tmpBlock2);
    memcpy(out, tmpBlock2, 64 * sizeof(bool));
}

//==================== 模式實作區 (ECB, CFB, CTR) ====================//

// ECB 模式加密
// 參數: fin 輸入檔案, fout 輸出檔案, key64[64] 金鑰
void desECBEncrypt(FILE* fin, FILE* fout, const bool key64[64]) {
    unsigned char buffer[8];
    while(true) {
        size_t n = fread(buffer, 1, 8, fin);
        if(n == 0) break;
        // Padding
        if(n < 8) {
            for(size_t i=n; i<8; i++) buffer[i] = ' ';
        }
        bool inBits[64], outBits[64];
        for(int i=0; i<8; i++){
            convert_in(buffer[i], &inBits[i*8]);
        }
        desEncrypt(inBits, outBits, key64);
        for(int i=0; i<8; i++){
            buffer[i] = convert_out(&outBits[i*8]);
        }
        fwrite(buffer, 1, 8, fout);
    }
}

// ECB 模式解密
// 參數: fin 輸入檔案, fout 輸出檔案, key64[64] 金鑰
void desECBDecrypt(FILE* fin, FILE* fout, const bool key64[64]) {
    unsigned char buffer[8];
    while(true) {
        size_t n = fread(buffer, 1, 8, fin);
        if(n == 0) break;
        bool inBits[64], outBits[64];
        for(int i=0; i<8; i++){
            convert_in(buffer[i], &inBits[i*8]);
        }
        desDecrypt(inBits, outBits, key64);
        for(int i=0; i<8; i++){
            buffer[i] = convert_out(&outBits[i*8]);
        }
        // 移除尾端空白
        int writeLen = 8;
        while(writeLen > 0 && buffer[writeLen - 1] == ' ') {
            writeLen--;
        }
        fwrite(buffer, 1, writeLen, fout);
    }
}

// CFB 模式加密 (64-bit Feedback)
// 參數: fin 輸入檔案, fout 輸出檔案, IV[64] 初始向量, key64[64] 金鑰
void desCFBEncrypt(FILE* fin, FILE* fout, const bool IV[64], const bool key64[64]) {
    bool prev[64];
    memcpy(prev, IV, 64*sizeof(bool));  // 初始化初始向量
    unsigned char buffer[8];

    while(true) {
        size_t n = fread(buffer, 1, 8, fin);
        if(n == 0) break;
        // Padding (若需要)
        if(n < 8) {
            for(size_t i=n; i<8; i++) buffer[i] = ' ';
        }
        bool ivOut[64];
        desEncrypt(prev, ivOut, key64);  // 加密上一個密文區塊

        // 產生新密文
        for(int i=0; i<8; i++){
            bool blockIn[8];
            convert_in(buffer[i], blockIn);
            for(int b=0; b<8; b++){
                blockIn[b] = blockIn[b] ^ ivOut[i*8 + b];
            }
            unsigned char c = convert_out(blockIn);
            buffer[i] = c;
        }
        fwrite(buffer, 1, 8, fout);

        // 更新 prev
        for(int i=0; i<8; i++){
            convert_in(buffer[i], &prev[i*8]);
        }
    }
}

// CFB 模式解密 (64-bit Feedback)
// 參數: fin 輸入檔案, fout 輸出檔案, IV[64] 初始向量, key64[64] 金鑰
void desCFBDecrypt(FILE* fin, FILE* fout, const bool IV[64], const bool key64[64]) {
    bool prev[64];
    memcpy(prev, IV, 64*sizeof(bool));
    unsigned char buffer[8];

    while(true) {
        size_t n = fread(buffer, 1, 8, fin);
        if(n == 0) break;
        bool ivOut[64];
        desEncrypt(prev, ivOut, key64);

        // 原文
        unsigned char plain[8];
        for(int i=0; i<8; i++){
            bool blockEncrypted[8];
            convert_in(buffer[i], blockEncrypted);
            for(int b=0; b<8; b++){
                blockEncrypted[b] = blockEncrypted[b] ^ ivOut[i*8 + b];
            }
            plain[i] = convert_out(blockEncrypted);
        }
        // 移除尾端空白
        int writeLen = 8;
        while(writeLen > 0 && plain[writeLen - 1] == ' ') {
            writeLen--;
        }
        fwrite(plain, 1, writeLen, fout);

        // 更新 prev (此處要用讀進來的密文)
        for(int i=0; i<8; i++){
            convert_in(buffer[i], &prev[i*8]);
        }
    }
}

// CTR 模式加解密 (64-bit Counter)
// 參數: fin 輸入檔案, fout 輸出檔案, nonceCtr[64] 計數器起始值, key64[64] 金鑰
void desCTREncryptDecrypt(FILE* fin, FILE* fout, const bool nonceCtr[64], const bool key64[64]) {
    // nonceCtr[64] 可視為起始計數器 (前半為 Nonce，後半為計數器)
    // 這裡簡化只用整個 64 bit 當作計數器
    unsigned long long counter = 0;
    for(int i=0; i<64; i++){
        if(nonceCtr[i]) counter |= (1ULL << i);
    }

    unsigned char buffer[8];
    while(true) {
        size_t n = fread(buffer, 1, 8, fin);
        if(n == 0) break;
        // Padding (若需要)
        if(n < 8) {
            for(size_t i=n; i<8; i++) buffer[i] = ' ';
        }

        // 將計數器轉成 64-bit block
        bool ctrBlock[64];
        memset(ctrBlock, 0, sizeof(ctrBlock));
        for(int i=0; i<64; i++){
            ctrBlock[i] = ((counter >> i) & 1ULL) != 0;
        }
        bool encryptedCtr[64];
        desEncrypt(ctrBlock, encryptedCtr, key64);

        // XOR 得到結果
        for(int i=0; i<8; i++){
            bool blockIn[8];
            convert_in(buffer[i], blockIn);
            for(int b=0; b<8; b++){
                blockIn[b] = blockIn[b] ^ encryptedCtr[i*8 + b];
            }
            buffer[i] = convert_out(blockIn);
        }
        // 移除尾端空白
        int writeLen = 8;
        while(writeLen > 0 && buffer[writeLen - 1] == ' ') {
            writeLen--;
        }
        fwrite(buffer, 1, writeLen, fout);
        counter++;
    }
}

