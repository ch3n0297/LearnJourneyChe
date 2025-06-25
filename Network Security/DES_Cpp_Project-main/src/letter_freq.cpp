#include <iostream>
#include <iomanip>
#include <array>
#include <cctype>

int main() {
    std::array<size_t, 26> counts{};   // A–Z 計數
    char ch;
    size_t totalLetters = 0;

    // 讀取每個字元
    while (true) {
        int rc = std::cin.get();
        if (rc == EOF) break;
        ch = static_cast<char>(rc);
        if (std::isalpha(static_cast<unsigned char>(ch))) {
            char up = std::toupper(ch);
            counts[up - 'A'] += 1;
            totalLetters += 1;
        }
    }

    if (totalLetters == 0) {
        std::cerr << "No letters!\n";
        return 1;
    }

    std::cout << "Letter  Count  Frequency(%)\n";
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        size_t idx = letter - 'A';
        double freq = (static_cast<double>(counts[idx]) * 100.0) / static_cast<double>(totalLetters);
        std::cout << letter
                  << std::setw(8) << counts[idx]
                  << std::setw(12) << std::fixed << std::setprecision(2) << freq
                  << "\n";
    }

    return 0;
}
