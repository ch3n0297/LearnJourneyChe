#include <bits/stdc++.h>

using Matrix2x2 = std::array<std::array<int, 2>, 2>;

static int modulus = 29;

// 計算模逆
int modular_inverse(int value) {
    for (int candidate = 1; candidate < modulus; ++candidate) {
        if ((value * candidate) % modulus == 1) return candidate;
    }
    throw std::runtime_error("No modular inverse exists");
}

// 矩陣相乘
Matrix2x2 matrix_multiply(const Matrix2x2& lhs, const Matrix2x2& rhs) {
    Matrix2x2 result{};
    for (int row = 0; row < 2; ++row) {
        for (int col = 0; col < 2; ++col) {
            int sum = 0;
            for (int k = 0; k < 2; ++k) {
                sum = (sum + lhs[row][k] * rhs[k][col]) % modulus;
            }
            result[row][col] = sum;
        }
    }
    return result;
}

// 矩陣與向量相乘
std::array<int, 2> matrix_vector_multiply(const Matrix2x2& mat, const std::array<int, 2>& vec) {
    return {
        (mat[0][0] * vec[0] + mat[0][1] * vec[1]) % modulus,
        (mat[1][0] * vec[0] + mat[1][1] * vec[1]) % modulus
    };
}

// 矩陣反轉
Matrix2x2 matrix_inverse(const Matrix2x2& matrix) {
    int determinant = (matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) % modulus;
    if (determinant < 0) determinant += modulus;
    int invDeterminant = modular_inverse(determinant);

    Matrix2x2 inverseMatrix {{
        { matrix[1][1] * invDeterminant % modulus, (modulus - matrix[0][1]) * invDeterminant % modulus },
        { (modulus - matrix[1][0]) * invDeterminant % modulus, matrix[0][0] * invDeterminant % modulus }
    }};

    return inverseMatrix;
}

// 字元轉數字
int symbol_to_number(char ch) {
    if (ch >= 'A' && ch <= 'Z') return ch - 'A';
    if (ch == ',') return 26;
    if (ch == '.') return 27;
    if (ch == '?') return 28;
    return -1;
}

// 數字轉字元
char number_to_symbol(int num) {
    if (num < 26) return 'A' + num;
    return ",.?"[num - 26];
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        std::cerr << "Usage: enc|dec a b c d  < infile > outfile\n";
        return EXIT_FAILURE;
    }

    bool isEncryptMode = (std::string(argv[1]) == "enc");

    Matrix2x2 encryptionMatrix {{
        { std::stoi(argv[2]), std::stoi(argv[3]) },
        { std::stoi(argv[4]), std::stoi(argv[5]) }
    }};

    Matrix2x2 decryptionMatrix = matrix_inverse(encryptionMatrix);

    std::vector<int> encodedNumbers;
    char inputChar;
    while (std::cin.get(inputChar)) {
        if (inputChar == ' ') continue; // 忽略空白
        int numericValue = symbol_to_number(std::toupper(inputChar));
        if (numericValue != -1) {
            encodedNumbers.push_back(numericValue);
        }
    }

    // Padding 如需要
    if (encodedNumbers.size() % 2 != 0) {
        encodedNumbers.push_back(symbol_to_number(','));
    }

    // 處理每一組 block
    for (size_t idx = 0; idx < encodedNumbers.size(); idx += 2) {
        std::array<int, 2> block{ encodedNumbers[idx], encodedNumbers[idx + 1] };
        auto transformedBlock = isEncryptMode
                                    ? matrix_vector_multiply(encryptionMatrix, block)
                                    : matrix_vector_multiply(decryptionMatrix, block);

        std::cout << number_to_symbol(transformedBlock[0]) << number_to_symbol(transformedBlock[1]);
    }

    std::cout << "\n";
    return EXIT_SUCCESS;
}
