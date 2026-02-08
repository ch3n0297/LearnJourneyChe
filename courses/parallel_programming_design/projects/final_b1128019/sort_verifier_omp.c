
/*
 * sort_verifier_omp.c
 *
 * OpenMP parallel version of the serial sort verifier.
 * Keeps **identical CLI options** and **identical output format** to the
 * reference serial implementation, but accelerates the O(N) scan phase.
 *
 * Compile example:
 *   gcc -O3 -march=native -std=c11 -fopenmp -o sort_verify_omp sort_verifier_omp.c
 *
 * Typical run:
 *   OMP_NUM_THREADS=28 ./sort_verify_omp -i input.txt -k 512 -b 524288 -v -t
 */

#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <omp.h>

/* ---------- default parameters ---------- */
#define DEFAULT_K            512ULL
#define DEFAULT_BUFFER_BYTES (1ULL<<19)  /* 512 KiB */

static uint64_t K            = DEFAULT_K;
static size_t   BUFFER_SIZE  = DEFAULT_BUFFER_BYTES;
static int      VERBOSE      = 0;
static int      SHOW_TIME    = 0;

/* ------------- timer helper ------------- */
static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec*1e-9;
}

/* ------------- usage -------------------- */
static void usage(const char *prog)
{
    fprintf(stderr,
      "Usage: %s -i <input-file> [options]\n"
      "  -i <path> : (required) input file path\n"
      "  -k <size> : unsorted‑segment warning threshold (default %" PRIu64 ")\n"
      "  -b <bytes>: input buffer bytes (currently unused in text mode, default %zu)\n"
      "  -v        : verbose\n"
      "  -t        : print timing\n"
      "  -h        : help\n",
      prog, DEFAULT_K, (size_t)DEFAULT_BUFFER_BYTES);
}

/* ---------- simple text loader ---------- */
static int load_array_text(const char *path, uint64_t **out, uint64_t *n_out)
{
    FILE *fp = fopen(path, "r");
    if(!fp){ perror(path); return -1; }

    uint64_t N;
    if(fscanf(fp,"%" SCNu64, &N)!=1){
        fprintf(stderr,"Failed to read N from %s\n", path);
        fclose(fp); return -1;
    }

    uint64_t *A;
    if(posix_memalign((void**)&A,64,N*sizeof(uint64_t))){
        fprintf(stderr,"memalign failed for N=%" PRIu64 "\n",N);
        fclose(fp); return -1;
    }

    for(uint64_t i=0;i<N;i++){
        if(fscanf(fp,"%" SCNu64, &A[i])!=1){
            fprintf(stderr,"Bad input at index %" PRIu64 "\n", i);
            free(A); fclose(fp); return -1;
        }
    }
    fclose(fp);
    *out=A; *n_out=N;
    return 0;
}

/* --------------- main ------------------- */
int main(int argc,char **argv)
{
    const char *input_path=NULL;
    int opt;
    while((opt=getopt(argc,argv,"i:k:b:vth"))!=-1){
        switch(opt){
            case 'i': input_path=optarg; break;
            case 'k': K=strtoull(optarg,NULL,10); break;
            case 'b': BUFFER_SIZE=strtoull(optarg,NULL,10); break;
            case 'v': VERBOSE=1; break;
            case 't': SHOW_TIME=1; break;
            case 'h': usage(argv[0]); return 0;
            default : usage(argv[0]); return 1;
        }
    }
    if(!input_path){ usage(argv[0]); return 1; }

    double t_start=now_sec();

    uint64_t *A=NULL, N=0;
    if(load_array_text(input_path,&A,&N)!=0) return 1;
    if(VERBOSE) fprintf(stderr,"[INFO] loaded N=%" PRIu64 "\n",N);

    /* -------- parallel scan for first inversion -------- */
    uint64_t global_inv = UINT64_MAX;

    #pragma omp parallel
    {
        uint64_t local_inv = UINT64_MAX;
        /* dynamic scheduling with medium chunk for load balance */
        #pragma omp for schedule(dynamic, 1<<18)
        for(uint64_t i=0;i<N-1;i++){
            if(A[i] > A[i+1]){
                local_inv = i;
                /* break out of loop early for this thread */
                #pragma omp cancel for
            }
        }
        /* reduction: keep smallest index */
        #pragma omp critical
        {
            if(local_inv < global_inv) global_inv = local_inv;
        }
    }

    if(global_inv==UINT64_MAX){
        puts("Array is sorted. PASS.");
        if(SHOW_TIME){
            printf("[TIME] total elapsed = %.6f sec\n", now_sec()-t_start);
        }
        free(A); return 0;
    }

    /* ---------- expand segment like serial ---------- */
    printf("Array is NOT sorted.\n");
    printf("First adjacent inversion at index inv_idx = %" PRIu64
           " (A[%" PRIu64 "] = %" PRIu64 ", A[%" PRIu64 "] = %" PRIu64 ").\n",
           global_inv, global_inv, A[global_inv], global_inv+1, A[global_inv+1]);

    uint64_t l=global_inv, r=global_inv+1;
    while(l>0 && A[l-1] > A[l]) --l;
    while(r+1<N && A[r] > A[r+1]) ++r;

    uint64_t seg_len = r-l+1;
    printf("Unsorted segment = [%" PRIu64 ", %" PRIu64 "], length = %" PRIu64 ".\n",
           l,r,seg_len);
    if(seg_len > K){
        printf("WARNING: segment length %" PRIu64 " > K (%" PRIu64 ").\n"
               "Consider splitting into smaller chunks of length <= K for後續處理。\n",
               seg_len, K);
    }

    if(VERBOSE){
        uint64_t lp = (l>=2? l-2:0);
        uint64_t rp = (r+2 < N ? r+2 : N-1);
        printf("[VERBOSE] Around l (index %" PRIu64 "): ", l);
        for(uint64_t i=lp; i<=l+2 && i<N; ++i) printf("%" PRIu64 " ", A[i]);
        printf("\n[VERBOSE] Around r (index %" PRIu64 "): ", r);
        for(uint64_t i=(r>=2? r-2:0); i<=rp; ++i) printf("%" PRIu64 " ", A[i]);
        printf("\n");
    }

    if(SHOW_TIME){
        printf("[TIME] total elapsed = %.6f sec\n", now_sec()-t_start);
    }

    free(A);
    return 0;
}