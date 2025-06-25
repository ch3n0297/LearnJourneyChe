#include <iostream>
#include <cstdint>

uint64_t fastExp(uint64_t x, uint64_t y, uint64_t p) {
    // 結果初始化為 1 % p
    uint64_t result = 1 % p;
    uint64_t baseVal = x % p;
    
    while (y > 0) {
        // 如果當前指數的最低位為 1，就乘上 baseVal
        if (y & 1ULL) {
            // 使用 __uint128_t 防止中間乘法溢位
            __uint128_t tmp = static_cast<__uint128_t>(result) * baseVal;
            result = static_cast<uint64_t>(tmp % p);
        }
        // baseVal = baseVal^2 % p
        __uint128_t sq = static_cast<__uint128_t>(baseVal) * baseVal;
        baseVal = static_cast<uint64_t>(sq % p);
        // 右移一位相當於除以 2
        y >>= 1;
    }
    return result;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: <program> base exponent modulus\n";
        return 1;
    }

    uint64_t b = std::stoull(argv[1]);
    uint64_t e = std::stoull(argv[2]);
    uint64_t m = std::stoull(argv[3]);

    uint64_t output = fastExp(b, e, m);
    std::cout << output << "\n";
    return 0;
}
