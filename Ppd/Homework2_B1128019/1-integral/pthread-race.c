#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// 可依需求調整
#define NUM_THREADS 4
#define NITERS 1000000

// 全域變數 sum，所有 threads 都會同時對它進行 sum += 1 操作
long long sum = 0;

// 每個執行緒要做的事情：重複執行 sum += 1
void* thread_func(void* arg) {
    for (long long i = 0; i < NITERS; i++) {
        // 注意：此處沒有任何同步保護
        // 可能導致多個 thread 同時讀取 / 寫入 sum，產生不預期結果
        sum += 1;
    }
    pthread_exit(NULL);
}

int main(int argc, char* argv[])
{
    pthread_t threads[NUM_THREADS];

    // 建立 threads
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_create(&threads[t], NULL, thread_func, NULL);
    }

    // 等待所有 threads 完成
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }

    // 理論上，最終 sum 應為 NUM_THREADS * NITERS
    long long expected = (long long)NUM_THREADS * NITERS;

    printf("Final sum (with race condition): %lld\n", sum);
    printf("Expected: %lld\n", expected);

    return 0;
}

