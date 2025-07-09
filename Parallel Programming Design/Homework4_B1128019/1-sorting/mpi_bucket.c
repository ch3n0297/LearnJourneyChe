

/*******************************************************
 * mpi_bucket.c
 *
 * Parallel bucket‑sort (range partitioning) + insertion
 * sort using MPI.  Designed for Taiwania 3 “ctest” queue.
 *
 *  • N = 50 000 random double values ∈ [0, 100] (2 dec).
 *  • Rank 0 generates data and broadcasts to all ranks.
 *  • Each rank selects values that fall inside its bucket
 *    range, sorts them locally with insertion sort,
 *    and sends the sorted sub‑array back to rank 0.
 *  • Rank 0 concatenates buckets → globally sorted list.
 *
 * Compare:
 *  – CPU  compute time   (local sorting)
 *  – COMM communication time (MPI Bcast + GatherV)
 *  – TOTAL wall‑clock time (overall)
 *******************************************************/
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define N 50000                    /* total numbers */
#define MAX_VAL 100.0              /* upper bound of generated numbers */

/* ---------- insertion sort ---------- */
static void insertion_sort(double *arr, int n) {
    for (int i = 1; i < n; ++i) {
        double key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            --j;
        }
        arr[j + 1] = key;
    }
}

/* ---------- main ---------- */
int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int world_size, world_rank;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    /* timers */
    double t_start_total = MPI_Wtime();
    double comm_time = 0.0, comp_time = 0.0;

    /* Allocate buffer for the whole dataset (all ranks need it for simplicity) */
    double *data = (double *)malloc(N * sizeof(double));
    if (!data) {
        fprintf(stderr, "Rank %d: Memory allocation failed\n", world_rank);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    /* ---------- generation & broadcast ---------- */
    if (world_rank == 0) {
        srand((unsigned int)time(NULL));
        for (int i = 0; i < N; ++i) {
            double r = (double)rand() / RAND_MAX;      /* 0–1 */
            r = round(r * 10000.0) / 100.0;            /* 0.00–100.00 */
            data[i] = r;
        }
    }

    double t_bcast_start = MPI_Wtime();
    MPI_Bcast(data, N, MPI_DOUBLE, /*root=*/0, MPI_COMM_WORLD);
    comm_time += MPI_Wtime() - t_bcast_start;

    /* Each rank owns a value‑range bucket:
       Bucket i covers [ i*Δ , (i+1)*Δ ), except the last bucket
       which includes the upper bound. */
    double delta = MAX_VAL / world_size;
    double lower = world_rank * delta;
    double upper = (world_rank == world_size - 1) ? MAX_VAL : (world_rank + 1) * delta;

    /* --------- select local elements ---------- */
    /* Rough upper bound for local allocation: N/world_size + slack */
    int alloc = (N / world_size) + 128;
    double *local = (double *)malloc(alloc * sizeof(double));
    if (!local) {
        fprintf(stderr, "Rank %d: local alloc failed\n", world_rank);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    int local_count = 0;
    for (int i = 0; i < N; ++i) {
        double v = data[i];
        int take = (v >= lower) && ( (world_rank == world_size-1) ? (v <= upper) : (v < upper) );
        if (take) {
            if (local_count >= alloc) {               /* expand buffer if needed */
                alloc *= 2;
                local = (double *)realloc(local, alloc * sizeof(double));
                if (!local) {
                    fprintf(stderr, "Rank %d: realloc failed\n", world_rank);
                    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
                }
            }
            local[local_count++] = v;
        }
    }

    /* ---------- local sort ---------- */
    double t_sort_start = MPI_Wtime();
    insertion_sort(local, local_count);
    comp_time = MPI_Wtime() - t_sort_start;

    /* ---------- gather counts ---------- */
    int *recvcounts = NULL;
    if (world_rank == 0) {
        recvcounts = (int *)malloc(world_size * sizeof(int));
    }
    double t_gather_start = MPI_Wtime();
    MPI_Gather(&local_count, 1, MPI_INT,
               recvcounts, 1, MPI_INT,
               0, MPI_COMM_WORLD);
    comm_time += MPI_Wtime() - t_gather_start;

    /* ---------- gather values with Gatherv ---------- */
    double *sorted = NULL;
    int *displs = NULL;
    if (world_rank == 0) {
        /* compute displacements */
        displs = (int *)malloc(world_size * sizeof(int));
        displs[0] = 0;
        for (int i = 1; i < world_size; ++i) {
            displs[i] = displs[i - 1] + recvcounts[i - 1];
        }
        int total_elems = displs[world_size - 1] + recvcounts[world_size - 1];
        sorted = (double *)malloc(total_elems * sizeof(double));
    }

    t_gather_start = MPI_Wtime();
    MPI_Gatherv(local, local_count, MPI_DOUBLE,
                sorted, recvcounts, displs, MPI_DOUBLE,
                0, MPI_COMM_WORLD);
    comm_time += MPI_Wtime() - t_gather_start;

    /* ---------- output & verification (rank 0) ---------- */
    if (world_rank == 0) {
        /* Print first 10 numbers */
        printf("First 10 sorted numbers:\n");
        for (int i = 0; i < 10 && i < N; ++i) {
            printf("%.2f ", sorted[i]);
        }
        printf("\n");

        /* sanity check for global ordering at few random spots */
        int errors = 0;
        for (int i = 1; i < N; ++i) {
            if (sorted[i] < sorted[i - 1]) {
                errors = 1;
                break;
            }
        }
        printf("Verification: %s\n", errors ? "FAILED" : "PASSED");

        /* timing report */
        double t_total = MPI_Wtime() - t_start_total;
        printf("CPU compute  time (local sort)   : %.6f s\n", comp_time);
        printf("COMM overhead time (Bcast+Gather): %.6f s\n", comm_time);
        printf("TOTAL wall‑clock time            : %.6f s\n", t_total);
    }

    /* ---------- cleanup ---------- */
    free(data);
    free(local);
    if (world_rank == 0) {
        free(sorted);
        free(recvcounts);
        free(displs);
    }

    MPI_Finalize();
    return 0;
}