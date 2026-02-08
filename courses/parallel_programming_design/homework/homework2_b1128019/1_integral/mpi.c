#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpi.h>

static inline double func(double x) {
    // sin(x)/x，x=0時視為極限值 1.0
    return (fabs(x) < 1e-15) ? 1.0 : sin(x) / x;
}

int main(int argc, char* argv[])
{
    // 可改為從命令列參數或檔案讀取
    const double L = 100.0;
    const long   N = 100000000;  // 預設1e8，可視資源調整

    MPI_Init(&argc, &argv);

    int world_rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    double start_time = MPI_Wtime();  // 紀錄起始時間(壁鐘)

    // 每段寬度 dx
    double dx = (2.0 * L) / (double)N;

    // 平分給每個 process 的區段大小 (此處假設 N 可以被 world_size 整除)
    long local_N = N / world_size;

    // 計算當前 process 負責的子區間 [start_i, end_i)
    long start_i = world_rank * local_N;
    long end_i   = start_i + local_N;

    // 對該子區間做積分
    double local_sum = 0.0;
    for (long i = start_i; i < end_i; i++) {
        double x_i = -L + (i + 0.5) * dx; // midpoint
        local_sum += func(x_i);
    }
    double local_integral = local_sum * dx;

    // 將各 process 的部分積分加總到 root process (rank=0)
    double global_integral = 0.0;
    MPI_Reduce(&local_integral, &global_integral, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    double end_time = MPI_Wtime();  // 紀錄結束時間(壁鐘)
    double elapsed_time = end_time - start_time;

    // 只有 root process 輸出結果
    if (world_rank == 0) {
        printf("Approximated value of integral: %.6f\n", global_integral);
        printf("Execution time (wall-clock): %.6f s\n", elapsed_time);
    }

    MPI_Finalize();
    return 0;
}

