#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <pthread.h>
#include <sys/time.h>   // for gettimeofday()

//--------------------------------------------
// 可自行調整 THREAD 數量
//--------------------------------------------
#define NUM_THREADS 4

//--------------------------------------------
// 函式：sin(x)/x，處理 x=0 極限值
//--------------------------------------------
double func(double x) {
    if (fabs(x) < 1e-15) {
        return 1.0;  // limit of sin(x)/x as x -> 0
    }
    return sin(x) / x;
}

//--------------------------------------------
// 全域變數: 供 threads 存放各自的局部積分結果
// 主程式會在最後加總 partial_sums[] 取得總積分
//--------------------------------------------
double *partial_sums;

//--------------------------------------------
// 傳遞給每個 thread 的參數結構
//--------------------------------------------
typedef struct {
    long start_idx;
    long end_idx;
    double dx;
    double L;
    int thread_id;
} ThreadData;

//--------------------------------------------
// Thread 函式
//--------------------------------------------
void* thread_func(void* arg)
{
    ThreadData *td = (ThreadData*) arg;
    double local_sum = 0.0;

    for (long i = td->start_idx; i < td->end_idx; i++) {
        double x_i = -td->L + (i + 0.5) * td->dx;
        local_sum += func(x_i);
    }
    // 將局部 sum 乘上 dx 存進 partial_sums
    partial_sums[td->thread_id] = local_sum * td->dx;

    pthread_exit(NULL);
}

int main(int argc, char* argv[])
{
    //-------------------------------
    // 設定問題參數 (可改成參數讀取)
    //-------------------------------
    const double L = 100.0;
    const long   N = 100000000;   // 1e8，可依需求調整
    // 假設 N 能被 NUM_THREADS 整除，若否則需做額外處理
    long chunk = N / NUM_THREADS; 

    // 配置存放各 thread 結果的陣列
    partial_sums = (double*) malloc(NUM_THREADS * sizeof(double));

    //-------------------------------
    // 紀錄開始時間 (壁鐘) 
    //-------------------------------
    struct timeval start_time, end_time;
    gettimeofday(&start_time, NULL);

    //-------------------------------
    // 創立 threads
    //-------------------------------
    pthread_t threads[NUM_THREADS];
    ThreadData tdata[NUM_THREADS];

    double dx = (2.0 * L) / (double)N;

    for (int t = 0; t < NUM_THREADS; t++) {
        tdata[t].thread_id  = t;
        tdata[t].L          = L;
        tdata[t].dx         = dx;
        tdata[t].start_idx  = t * chunk;
        tdata[t].end_idx    = (t+1) * chunk;
        pthread_create(&threads[t], NULL, thread_func, (void*)&tdata[t]);
    }

    //-------------------------------
    // 等待所有 threads 完成
    //-------------------------------
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }

    //-------------------------------
    // 將所有 thread 的局部積分相加
    //-------------------------------
    double total_sum = 0.0;
    for (int t = 0; t < NUM_THREADS; t++) {
        total_sum += partial_sums[t];
    }

    //-------------------------------
    // 記錄結束時間 & 計算執行時間
    //-------------------------------
    gettimeofday(&end_time, NULL);
    double elapsed = (double)(end_time.tv_sec - start_time.tv_sec)
                   + (double)(end_time.tv_usec - start_time.tv_usec) * 1e-6;

    //-------------------------------
    // 印出結果
    //-------------------------------
    printf("Approximated value of integral: %.6f\n", total_sum);
    printf("Total (wall-clock) time: %.6f s\n", elapsed);

    // 釋放資源
    free(partial_sums);
    return 0;
}

