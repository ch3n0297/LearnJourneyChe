/********************************************************************
 * mpi_pipeline.c
 *
 * Pipelined merge‑sort with token termination
 * ------------------------------------------
 * 1. Rank 0 產生 N 個隨機 double (0–100, 小數二位)。
 * 2. 以 MPI_Scatterv 將資料平均切分給所有 rank，
 *    每個 rank 使用 insertion sort 先就地排序。
 * 3. 進入「Pipeline Merge」階段：
 *      – 第 0 號 rank 將自己的 sorted array 送到 rank 1，
 *        接著送一個終止 token (len = -1)。
 *      – rank i (1‥p‑2) 不斷接收 upstream 傳來的
 *        sorted sub‑array，與本地陣列 merge 成新的
 *        sorted 陣列，然後將結果再傳給 rank i+1。
 *        最後再把 token 轉發。
 *      – 最末 rank (p‑1) 收到最終結果，驗證排序後
 *        把整個 array 送回 rank 0 作為輸出。
 * 4. Rank 0 列印前 10 筆數據、驗證結果與耗時。
 *
 * 時間指標：
 *  • comp_time — insertion + 每次 merge 時的 CPU 時間
 *  • comm_time — pipeline 內部所有 MPI 傳輸時間
 *  • total      — 總 wall‑clock
 *
 * 編譯：  mpicc -O2 -o mpi_pipeline.out mpi_pipeline.c -lm
 ********************************************************************/
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define N 50000
#define MAX_VAL 100.0

/* ---------------- insertion sort ---------------- */
static void insertion_sort(double *a, int n) {
    for (int i = 1; i < n; ++i) {
        double key = a[i];
        int j = i - 1;
        while (j >= 0 && a[j] > key) {
            a[j + 1] = a[j];
            --j;
        }
        a[j + 1] = key;
    }
}

/* ---------------- merge two sorted arrays ----------------
   dst = sorted merge of A(size m) and B(size n).
   Return new total length.  (A and B are freed)          */
static double *merge_arrays(double *A, int m, double *B, int n) {
    double *C = (double *)malloc((m + n) * sizeof(double));
    int i = 0, j = 0, k = 0;
    while (i < m && j < n) {
        if (A[i] <= B[j])
            C[k++] = A[i++];
        else
            C[k++] = B[j++];
    }
    while (i < m) C[k++] = A[i++];
    while (j < n) C[k++] = B[j++];
    free(A);
    free(B);
    return C;  /* length = m + n */
}

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int p, rank;
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    /* --- timing helpers --- */
    double t0 = MPI_Wtime();
    double comp_time = 0.0, comm_time = 0.0;

    /* ---------------- data generation & Scatterv ---------------- */
    double *data = NULL;
    int *sendcounts = NULL, *displs = NULL;
    if (rank == 0) {
        data = (double *)malloc(N * sizeof(double));
        srand((unsigned int)time(NULL));
        for (int i = 0; i < N; ++i) {
            double r = (double)rand() / RAND_MAX;
            data[i] = round(r * 10000.0) / 100.0;  /* 0.00–100.00 */
        }

        /* decide chunk sizes */
        sendcounts = (int *)malloc(p * sizeof(int));
        displs     = (int *)malloc(p * sizeof(int));
        int base = N / p, rem = N % p;
        displs[0] = 0;
        for (int i = 0; i < p; ++i) {
            sendcounts[i] = base + (i < rem ? 1 : 0);
            if (i > 0) displs[i] = displs[i - 1] + sendcounts[i - 1];
        }
    }

    /* broadcast sendcounts to everybody for local alloc */
    int local_n;
    MPI_Scatter(sendcounts, 1, MPI_INT,
                &local_n, 1, MPI_INT,
                0, MPI_COMM_WORLD);

    double *local = (double *)malloc(local_n * sizeof(double));

    /* actual Scatterv */
    MPI_Scatterv(data, sendcounts, displs, MPI_DOUBLE,
                 local, local_n, MPI_DOUBLE,
                 0, MPI_COMM_WORLD);

    if (rank == 0) {
        free(data);
        free(sendcounts);
        free(displs);
    }

    /* ---------------- local sort ---------------- */
    double t_sort = MPI_Wtime();
    insertion_sort(local, local_n);
    comp_time += MPI_Wtime() - t_sort;

    /* ---------------- pipeline merge ---------------- */
    const int TAG_LEN = 0, TAG_DATA = 1;
    int len = local_n;
    double *arr = local;

    if (rank == 0) {
        /* send own chunk and then token to rank 1 */
        double t_send = MPI_Wtime();
        MPI_Send(&len, 1, MPI_INT, 1, TAG_LEN, MPI_COMM_WORLD);
        MPI_Send(arr, len, MPI_DOUBLE, 1, TAG_DATA, MPI_COMM_WORLD);
        int token = -1;
        MPI_Send(&token, 1, MPI_INT, 1, TAG_LEN, MPI_COMM_WORLD);
        comm_time += MPI_Wtime() - t_send;
        free(arr);  /* rank 0 no longer keeps local copy */

        /* receive final sorted array back from last rank */
        int final_len;
        MPI_Recv(&final_len, 1, MPI_INT, p - 1, TAG_LEN, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        double *final_arr = (double *)malloc(final_len * sizeof(double));
        MPI_Recv(final_arr, final_len, MPI_DOUBLE, p - 1, TAG_DATA, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

        /* verification */
        int ok = 1;
        for (int i = 1; i < final_len; ++i)
            if (final_arr[i] < final_arr[i - 1]) { ok = 0; break; }

        /* output */
        printf("First 10 sorted numbers:\n");
        for (int i = 0; i < 10 && i < final_len; ++i)
            printf("%.2f ", final_arr[i]);
        printf("\nVerification: %s\n", ok ? "PASSED" : "FAILED");

        double total = MPI_Wtime() - t0;
        printf("CPU compute time (local sort + merges): %.6f s\n", comp_time);
        printf("COMM time (pipeline transfers)         : %.6f s\n", comm_time);
        printf("TOTAL wall‑clock time                  : %.6f s\n", total);

        free(final_arr);

    } else {
        while (1) {
            int incoming_len;
            MPI_Recv(&incoming_len, 1, MPI_INT, rank - 1, TAG_LEN, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            if (incoming_len == -1) {  /* token => forward then break */
                if (rank != p - 1)
                    MPI_Send(&incoming_len, 1, MPI_INT, rank + 1, TAG_LEN, MPI_COMM_WORLD);
                break;
            }

            /* receive incoming sorted sub‑array */
            double *incoming = (double *)malloc(incoming_len * sizeof(double));
            MPI_Recv(incoming, incoming_len, MPI_DOUBLE, rank - 1, TAG_DATA, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            /* merge with local arr */
            double t_merge = MPI_Wtime();
            arr = merge_arrays(arr, len, incoming, incoming_len);
            len += incoming_len;
            comp_time += MPI_Wtime() - t_merge;

            /* forward merged result or store if last rank */
            double t_fw = MPI_Wtime();
            if (rank != p - 1) {
                MPI_Send(&len, 1, MPI_INT, rank + 1, TAG_LEN, MPI_COMM_WORLD);
                MPI_Send(arr, len, MPI_DOUBLE, rank + 1, TAG_DATA, MPI_COMM_WORLD);
                /* reset local to empty because we passed ownership */
                free(arr);
                arr = (double *)malloc(0);
                len = 0;
            }
            comm_time += MPI_Wtime() - t_fw;
        } /* end while */

        /* if last rank, send final array back to rank 0 */
        if (rank == p - 1) {
            MPI_Send(&len, 1, MPI_INT, 0, TAG_LEN, MPI_COMM_WORLD);
            MPI_Send(arr, len, MPI_DOUBLE, 0, TAG_DATA, MPI_COMM_WORLD);
        }

        free(arr);
    }

    /* ---------------- finalize ---------------- */
    double local_comp_comm[2] = { comp_time, comm_time };
    double global_comp_comm[2];
    MPI_Reduce(local_comp_comm, global_comp_comm, 2, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    MPI_Finalize();
    return 0;
}
