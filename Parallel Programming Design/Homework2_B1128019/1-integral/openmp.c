#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <omp.h>

static inline double func(double x) {
    // 處理 x=0 極限值
    return (fabs(x) < 1e-15) ? 1.0 : sin(x) / x;
}

int main(int argc, char* argv[])
{
    // 可視需求調整
    const double L = 100.0;
    const long   N = 100000000;   // 1e8
    double dx = (2.0 * L) / (double)N;

    // 可透過環境變數 OMP_NUM_THREADS 或程式內設定 thread 數量
    // eg. omp_set_num_threads(4);

    // 量測起始時間（壁鐘時間）
    double start_time = omp_get_wtime();

    double sum = 0.0;

    // 使用 OpenMP 平行化，對主要積分迴圈做 reduction
    #pragma omp parallel for reduction(+:sum)
    for (long i = 0; i < N; i++) {
        double x_i = -L + (i + 0.5) * dx;  // Midpoint
        sum += func(x_i);
    }

    // 乘上 dx 才是最終的積分近似
    sum *= dx;

    // 量測結束時間（壁鐘時間）
    double end_time = omp_get_wtime();
    double elapsed_time = end_time - start_time;

    // 輸出結果
    printf("Approximated value of integral: %.6f\n", sum);
    printf("Execution time (wall-clock): %.6f s\n", elapsed_time);

    return 0;
}

