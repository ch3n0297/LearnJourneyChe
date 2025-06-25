#include <iostream>
#include <vector>
#include <random>
#include <bitset>
#include <unordered_map>
#include <algorithm>
#include <numeric> // for std::iota

// 產生隨機排列
static std::vector<uint8_t> generate_mapping(int bits){
    size_t size = static_cast<size_t>(1u << bits); // 2^bits
    std::vector<uint8_t> mapping(size);
    std::iota(mapping.begin(), mapping.end(), 0);  // 填入 [0,1,2,...]
    
    std::mt19937 engine{std::random_device{}()};
    std::shuffle(mapping.begin(), mapping.end(), engine); // 打亂順序
    
    return mapping;
}

// 反向映射
static std::unordered_map<uint8_t, uint8_t> build_inverse_map(const std::vector<uint8_t>& mapping){
    std::unordered_map<uint8_t, uint8_t> inverse;
    size_t index = 0;
    for(const auto& value : mapping){
        inverse[value] = static_cast<uint8_t>(index++);
    }
    return inverse;
}

int main(int argc, char* argv[]){
    // 檢查參數
    if(argc != 3){
        std::cerr << "Usage: enc|dec n  < infile > outfile\n";
        return EXIT_FAILURE;
    }

    std::string mode(argv[1]);
    bool isEncrypting = (mode == "enc");
    int bitWidth = std::stoi(argv[2]);
    
    if(bitWidth <= 0 || bitWidth > 8){
        std::cerr << "n must be 1-8\n";
        return EXIT_FAILURE;
    }

    // 初始化 key 與 inverse key
    auto keyMap = generate_mapping(bitWidth);
    auto inverseMap = build_inverse_map(keyMap);

    std::bitset<8> bitBuffer;
    int count = 0;
    int inputChar;
    int blockValue;

    // 處理輸入資料
    while((inputChar = std::cin.get()) != EOF){
        bitBuffer <<= 1;
        bitBuffer.set(0, (inputChar != '0') ? true : false);

        ++count;
        if(count == bitWidth){
            uint8_t mappedValue = isEncrypting ? keyMap[bitBuffer.to_ulong()]
                                               : inverseMap[bitBuffer.to_ulong()];

            // 輸出 bits
            for(int i = bitWidth - 1; i >= 0; --i){
                std::cout << ((mappedValue >> i) & 1);
            }

            // 重置
            bitBuffer.reset();
            count = 0;
        }
    }

    // 檢查是否有遺失 block
    if(count > 0){
        std::cerr << "\n[WARN] Incomplete block ignored\n";
    }

    return EXIT_SUCCESS;
}
