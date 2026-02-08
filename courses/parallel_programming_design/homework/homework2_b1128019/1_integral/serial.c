#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>       // for clock()
#include <sys/time.h>   // for gettimeofday()

// f(x) = sin(x) / x，特別處理 x=0 的情況
double func(double x) {
    if (fabs(x) < 1e-15) {
        return 1.0; // limit sin(x)/x -> 1
    }
    return sin(x) / x;
}

int main(int argc, char *argv[]) {
    // 可以改成參數輸入，這裡示範直接定義
    const double L = 100.0;       // Truncation boundary
    const long   N = 10000000;    // Number of subintervals (可視需求調大或調小)
    
    // 記錄起始時間 (CPU)
    clock_t start_clock = clock();
    // 記錄起始時間 (壁鐘)
    struct timeval start_time, end_time;
    gettimeofday(&start_time, NULL);

    double dx = (2.0 * L) / (double)N;  // 每個小區間的寬度
    double sum = 0.0;                   // 積分和

    // Midpoint Rule 累加
    for (long i = 0; i < N; i++) {
        double x_i = -L + (i + 0.5) * dx; // mid-point
        sum += func(x_i);
    }
    sum *= dx; // 最後乘以 dx 即為近似積分值

    // 記錄結束時間 (CPU) 並計算差值
    clock_t end_clock = clock();
    double cpu_time_used = (double)(end_clock - start_clock) / CLOCKS_PER_SEC;

    // 記錄結束時間 (壁鐘) 並計算差值
    gettimeofday(&end_time, NULL);
    double wall_time_used = (double)(end_time.tv_sec - start_time.tv_sec)
                          + (double)(end_time.tv_usec - start_time.tv_usec) * 1e-6;

    // 輸出結果，保留小數點後六位
    printf("Approximated value of integral: %.6f\n", sum);
    printf("CPU time: %.6f s\n", cpu_time_used);
    printf("Total (wall) time: %.6f s\n", wall_time_used);

    return 0;
}

