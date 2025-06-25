#ifndef DES_H
#define DES_H

#include <cstdio>

// DES 加密/解密函數聲明
void desECBEncrypt(FILE* inputFile, FILE* outputFile, const bool key[64]);
void desECBDecrypt(FILE* inputFile, FILE* outputFile, const bool key[64]);
void desCFBEncrypt(FILE* inputFile, FILE* outputFile, const bool key[64], const bool iv[64]);
void desCFBDecrypt(FILE* inputFile, FILE* outputFile, const bool key[64], const bool iv[64]);
void desCTREncryptDecrypt(FILE* inputFile, FILE* outputFile, const bool key[64], const bool iv[64]);

#endif // DES_H
