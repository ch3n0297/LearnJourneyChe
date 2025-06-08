/*
mpicc -O3 -march=native -std=c11 -o sort_verify_mpi sort_verifier_mpi_d.c
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <mpi.h>
#include <inttypes.h>
#include <limits.h>

static int SHOW_TIME = 0;

#define TAG_REQ 1
#define TAG_JOB 2
#define TAG_RES 3
#define TAG_STOP 4

static double now_sec(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + 1e-6 * tv.tv_usec;
}

static void usage(const char *prog) {
    fprintf(stderr, "Usage: %s [-v] [-t] filename\n", prog);
    exit(1);
}

/* text file format:
 *   1st line : N
 *   next N   : N uint64_t values (space / newline separated)
 */
static uint64_t *load_array_from_text(const char *filename, uint64_t *pn) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error opening file %s\n", filename);
        exit(1);
    }

    uint64_t N;
    if (fscanf(fp, "%" SCNu64, &N) != 1) {
        fprintf(stderr, "Failed to read N from %s\n", filename);
        fclose(fp);
        exit(1);
    }

    uint64_t *A = malloc(N * sizeof(uint64_t));
    if (!A) {
        fprintf(stderr, "malloc failed for %" PRIu64 " elements\n", N);
        fclose(fp);
        exit(1);
    }

    for (uint64_t i = 0; i < N; ++i) {
        if (fscanf(fp, "%" SCNu64, &A[i]) != 1) {
            fprintf(stderr, "Bad data at element %" PRIu64 " in %s\n", i, filename);
            free(A); fclose(fp); exit(1);
        }
    }
    fclose(fp);
    *pn = N;
    return A;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    int verbose = 0;
    const char *filename = NULL;
    if (rank == 0) {
        // parse args
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "-v") == 0) {
                verbose = 1;
            } else if (strcmp(argv[i], "-t") == 0) {
                SHOW_TIME = 1;
            } else if (argv[i][0] == '-') {
                usage(argv[0]);
            } else {
                filename = argv[i];
            }
        }
        if (!filename) usage(argv[0]);
    }

    // Broadcast verbose flag and filename length then filename to all ranks
    MPI_Bcast(&verbose, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&SHOW_TIME, 1, MPI_INT, 0, MPI_COMM_WORLD);
    int fname_len = 0;
    if (rank == 0) fname_len = (int)strlen(filename);
    MPI_Bcast(&fname_len, 1, MPI_INT, 0, MPI_COMM_WORLD);
    char fname_buf[1024];
    if (rank == 0) {
        strncpy(fname_buf, filename, sizeof(fname_buf));
        fname_buf[sizeof(fname_buf)-1] = 0;
    }
    MPI_Bcast(fname_buf, fname_len, MPI_CHAR, 0, MPI_COMM_WORLD);
    fname_buf[fname_len] = 0;
    if (rank != 0) filename = fname_buf;

    uint64_t *A = NULL;
    uint64_t N = 0;

    double start_t = 0.0;

    if (rank == 0) {
        start_t = now_sec();
        A = load_array_from_text(filename, &N);
    }

    // Broadcast N to all ranks
    MPI_Bcast(&N, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);

    // Broadcast array A from root to all ranks after N is known
    if (N > 0) {
        if (rank != 0) {
            A = malloc(N * sizeof(uint64_t));
            if (!A) {
                fprintf(stderr, "rank %d malloc failed\n", rank);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
        }
        MPI_Bcast(A, N, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    }

    if (rank != 0) {
        start_t = now_sec();   /* workers start timing after they have data */
    }

    MPI_Barrier(MPI_COMM_WORLD);

    // Define chunk size
    uint64_t CHUNK = 4*1024*1024;
    if (N < CHUNK) CHUNK = N;

    if (rank == 0) {
        uint64_t next_start = 0;
        uint64_t inv_idx_min = UINT64_MAX;
        int active_workers   = world_size - 1;      /* workers still running */

        MPI_Status st;

        while (active_workers > 0) {
            /* Receive either a request or a result from any worker */
            MPI_Probe(MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &st);

            if (st.MPI_TAG == TAG_REQ) {
                /* consume the zero‑byte request */
                MPI_Recv(NULL, 0, MPI_CHAR, st.MPI_SOURCE, TAG_REQ, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

                uint64_t msg[2];
                if (next_start >= N - 1) {
                    /* no more work ‑‑ send stop */
                    msg[0] = msg[1] = UINT64_MAX;
                    MPI_Send(msg, 2, MPI_UINT64_T, st.MPI_SOURCE, TAG_STOP, MPI_COMM_WORLD);
                    active_workers--;
                } else {
                    uint64_t start = next_start;
                    uint64_t end   = start + CHUNK;
                    if (end > N - 1) end = N - 1;
                    msg[0] = start;
                    msg[1] = end;
                    MPI_Send(msg, 2, MPI_UINT64_T, st.MPI_SOURCE, TAG_JOB, MPI_COMM_WORLD);
                    next_start = end;
                }
            } else if (st.MPI_TAG == TAG_RES) {
                uint64_t idx;
                MPI_Recv(&idx, 1, MPI_UINT64_T, st.MPI_SOURCE, TAG_RES, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                if (idx != UINT64_MAX && idx < inv_idx_min)
                    inv_idx_min = idx;
            }
        }

        /* ----- output identical to serial ----- */
        if (inv_idx_min == UINT64_MAX) {
            printf("Array is sorted. PASS.\n");
        } else {
            printf("Array is NOT sorted.\n");
            printf("First adjacent inversion at index inv_idx = %" PRIu64
                   " (A[%" PRIu64 "] = %" PRIu64 ", A[%" PRIu64 "] = %" PRIu64 ").\n",
                   inv_idx_min, inv_idx_min, A[inv_idx_min],
                   inv_idx_min + 1, A[inv_idx_min + 1]);

            uint64_t l = inv_idx_min, r = inv_idx_min + 1;
            while (l > 0 && A[l - 1] > A[l]) --l;
            while (r + 1 < N && A[r] > A[r + 1]) ++r;

            printf("Unsorted segment = [%" PRIu64 ", %" PRIu64 "], length = %" PRIu64 ".\n",
                   l, r, r - l + 1);
        }

        if (SHOW_TIME) {
            double end_t = now_sec();
            printf("[TIME] total elapsed = %.6f sec\n", end_t - start_t);
        }

        if (verbose) {
            double end_t = now_sec();
            fprintf(stderr, "Elapsed %.6f s with %d ranks\n", end_t - start_t, world_size);
        }
        free(A);
    } else {
        // Worker ranks
        MPI_Status status;
        while (1) {
            // send request
            MPI_Send(NULL, 0, MPI_CHAR, 0, TAG_REQ, MPI_COMM_WORLD);
            // receive job
            uint64_t job[2];
            MPI_Recv(job, 2, MPI_UINT64_T, 0, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
            if (status.MPI_TAG == TAG_STOP) {
                // done
                break;
            }
            uint64_t start = job[0];
            uint64_t end = job[1];

            // scan segment
            uint64_t inv_idx = UINT64_MAX;
            if (start > 0) {
                if (A[start-1] > A[start]) {
                    inv_idx = start-1;
                }
            }
            for (uint64_t i = start; i < end; i++) {
                if (A[i] > A[i+1]) {
                    inv_idx = i;
                    break;
                }
            }
            MPI_Send(&inv_idx, 1, MPI_UINT64_T, 0, TAG_RES, MPI_COMM_WORLD);
        }
        free(A);
    }

    MPI_Finalize();
    return 0;
}
