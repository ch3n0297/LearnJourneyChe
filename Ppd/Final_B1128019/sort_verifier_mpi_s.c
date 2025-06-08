/*
 * sort_verifier_mpi_s.c  ―  MPI (static partition) sort‑verifier
 *
 * Compile:
 *   mpicc -O3 -march=native -std=c11 -o sort_verify_mpi_s sort_verifier_mpi_s.c
 *
 * Each rank gets a fixed contiguous block of the array
 * [start, end) = [ N*rank/size , N*(rank+1)/size )
 * and scans it (plus the cross‑boundary pair (start‑1,start) if start>0).
 * A global MPI_Reduce(MIN) yields the first inversion index.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
#include <mpi.h>
#include <sys/time.h>

static int SHOW_TIME = 0;

static double now_sec(void){
    struct timeval tv; gettimeofday(&tv,NULL);
    return tv.tv_sec + tv.tv_usec*1e-6;
}

static void usage(const char *p){
    fprintf(stderr,"Usage: %s [-v] [-t] <input-txt>\n",p); exit(EXIT_FAILURE);
}

/* text loader:
 *   first line : N (number of elements)
 *   following  : N uint64_t numbers separated by whitespace
 */
static uint64_t *load_txt(const char *path, uint64_t *pn){
    FILE *fp = fopen(path,"r");
    if(!fp){ perror(path); exit(EXIT_FAILURE); }

    uint64_t N;
    if(fscanf(fp,"%" SCNu64,&N)!=1){
        fprintf(stderr,"Failed to read N from %s\n",path);
        fclose(fp); exit(EXIT_FAILURE);
    }

    uint64_t *A = malloc(N*sizeof(uint64_t));
    if(!A){ fprintf(stderr,"malloc failed for %" PRIu64 " elems\n",N); fclose(fp); exit(EXIT_FAILURE); }

    for(uint64_t i=0;i<N;i++){
        if(fscanf(fp,"%" SCNu64,&A[i])!=1){
            fprintf(stderr,"Bad data at element %" PRIu64 " in %s\n", i, path);
            free(A); fclose(fp); exit(EXIT_FAILURE);
        }
    }
    fclose(fp);
    *pn = N;
    return A;
}

int main(int argc,char **argv){
    MPI_Init(&argc,&argv);
    int rank,size; MPI_Comm_rank(MPI_COMM_WORLD,&rank);
    MPI_Comm_size(MPI_COMM_WORLD,&size);

    /* ---- arg parse (root) ---- */
    int verbose=0; const char *fname=NULL;
    if(rank==0){
        for(int i=1;i<argc;i++){
            if(!strcmp(argv[i],"-v")) verbose=1;
            else if(!strcmp(argv[i],"-t")) SHOW_TIME=1;
            else if(argv[i][0]=='-') usage(argv[0]);
            else fname=argv[i];
        }
        if(!fname) usage(argv[0]);
    }
    MPI_Bcast(&verbose,1,MPI_INT,0,MPI_COMM_WORLD);
    MPI_Bcast(&SHOW_TIME,1,MPI_INT,0,MPI_COMM_WORLD);

    /* broadcast filename to all for completeness (not actually used by workers) */
    int fn_len= (rank==0)? (int)strlen(fname):0;
    MPI_Bcast(&fn_len,1,MPI_INT,0,MPI_COMM_WORLD);
    char fn_buf[1024]="";
    if(rank==0){ strncpy(fn_buf,fname,sizeof(fn_buf)-1); }
    MPI_Bcast(fn_buf,fn_len,MPI_CHAR,0,MPI_COMM_WORLD);
    if(rank!=0) fname=fn_buf;

    /* ---- load & broadcast data ---- */
    uint64_t *A=NULL,N=0;
    double t0 = 0.0;      /* timer starts after data ready */
    if(rank==0) t0 = now_sec();   /* root includes load+broadcast */
    if(rank==0) A=load_txt(fname,&N);
    MPI_Bcast(&N,1,MPI_UINT64_T,0,MPI_COMM_WORLD);
    if(rank!=0){
        A=malloc(N*sizeof(uint64_t));
        if(!A){fprintf(stderr,"rank %d malloc failed\n",rank); MPI_Abort(MPI_COMM_WORLD,1);}
    }
    MPI_Bcast(A,N,MPI_UINT64_T,0,MPI_COMM_WORLD);
    if(rank!=0) t0 = now_sec();   /* workers start timing after they receive data */
    MPI_Barrier(MPI_COMM_WORLD);               /* sync before timing */

    /* ---- static partition ---- */
    uint64_t start = (N * (uint64_t)rank)       / (uint64_t)size;
    uint64_t end   = (N * (uint64_t)(rank+1))   / (uint64_t)size; /* exclusive */
    if(end<start) end=start;                    /* safety */

    uint64_t local_min = UINT64_MAX;

    /* cross‑boundary pair */
    if(start>0 && A[start-1] > A[start]) local_min=start-1;

    /* scan [start, end-1) comparing A[i] vs A[i+1]; ensure i+1<N */
    for(uint64_t i=start; i+1<N && i<end; ++i){
        if(A[i] > A[i+1]){ local_min=i; break; }
    }

    uint64_t global_min;
    MPI_Reduce(&local_min,&global_min,1,MPI_UINT64_T,MPI_MIN,0,MPI_COMM_WORLD);

    /* ---- root outputs result ---- */
    if(rank==0){
        if(global_min==UINT64_MAX){
            printf("Array is sorted. PASS.\n");
            if(SHOW_TIME){
                double t1 = now_sec();
                printf("[TIME] total elapsed = %.6f sec\n", t1 - t0);
            }
        }else{
            /* expand unsorted segment */
            uint64_t l=global_min, r=global_min+1;
            while(l>0      && A[l-1] > A[l]) --l;
            while(r+1<N && A[r]   > A[r+1]) ++r;
            printf("Array is NOT sorted.\n");
            printf("First adjacent inversion at index inv_idx = %" PRIu64 " (A[%" PRIu64 "] = %" PRIu64 ", A[%" PRIu64 "] = %" PRIu64 ").\n",
                   global_min, global_min, A[global_min], global_min+1, A[global_min+1]);
            printf("Unsorted segment = [%" PRIu64 ", %" PRIu64 "], length = %" PRIu64 ".\n",
                   l,r,r-l+1);
            if(SHOW_TIME){
                double t1 = now_sec();
                printf("[TIME] total elapsed = %.6f sec\n", t1 - t0);
            }
        }
        if(verbose){
            double t1_v = now_sec();
            fprintf(stderr,"Elapsed %.6f s with %d ranks\n", t1_v - t0, size);
        }
        free(A);
    }else{
        free(A);
    }
    MPI_Finalize();
    return 0;
}