#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#define N 100000
int main(int argc, char **argv){
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    double start_total = MPI_Wtime();
    double comp_time = 0.0, comm_time = 0.0;
    long rows_per_proc = N / size;
    long extra = N % size;
    long start_row = rank * rows_per_proc + (rank < extra ? rank : extra);
    long local_n = rows_per_proc + (rank < extra ? 1 : 0);
    int local_firstA[10][10], local_firstB[10][10], local_firstC[10][10];
    int local_lastA = 0, local_lastB = 0, local_lastC = 0;
    int has_last = 0;
    for(long i = 0; i < local_n; i++){
        long global_i = start_row + i;
        int *A = (int*)malloc(N * sizeof(int));
        int *B = (int*)malloc(N * sizeof(int));
        int *C = (int*)malloc(N * sizeof(int));
        for(long j = 0; j < N; j++){
            A[j] = rand();
            B[j] = rand();
        }
        double start_comp = MPI_Wtime();
        for(long j = 0; j < N; j++){
            C[j] = A[j] + B[j];
        }
        double end_comp = MPI_Wtime();
        comp_time += (end_comp - start_comp);
        if(global_i < 10){
            for(int j = 0; j < 10; j++){
                local_firstA[global_i][j] = A[j];
                local_firstB[global_i][j] = B[j];
                local_firstC[global_i][j] = C[j];
            }
        }
        if(global_i == N - 1){
            local_lastA = A[N - 1];
            local_lastB = B[N - 1];
            local_lastC = C[N - 1];
            has_last = 1;
        }
        free(A);
        free(B);
        free(C);
    }
    double end_total = MPI_Wtime();
    double local_total = end_total - start_total;
    double local_io = local_total - comp_time;
    int global_firstA[10][10], global_firstB[10][10], global_firstC[10][10];
    int global_lastA = 0, global_lastB = 0, global_lastC = 0;
    if(rank == 0){
        for(long i = 0; i < local_n; i++){
            long global_i = start_row + i;
            if(global_i < 10){
                for(int j = 0; j < 10; j++){
                    global_firstA[global_i][j] = local_firstA[global_i][j];
                    global_firstB[global_i][j] = local_firstB[global_i][j];
                    global_firstC[global_i][j] = local_firstC[global_i][j];
                }
            }
            if(global_i == N - 1){
                global_lastA = local_lastA;
                global_lastB = local_lastB;
                global_lastC = local_lastC;
            }
        }
        for(int i = 0; i < 10; i++){
            if(i < start_row || i >= start_row + local_n){
                int buf[30];
                double t = MPI_Wtime();
                MPI_Recv(buf, 30, MPI_INT, MPI_ANY_SOURCE, i, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                comm_time += MPI_Wtime() - t;
                for(int j = 0; j < 10; j++){
                    global_firstA[i][j] = buf[j];
                    global_firstB[i][j] = buf[10 + j];
                    global_firstC[i][j] = buf[20 + j];
                }
            }
        }
        if(!(start_row <= N - 1 && N - 1 < start_row + local_n)){
            int buf[3];
            double t = MPI_Wtime();
            MPI_Recv(buf, 3, MPI_INT, MPI_ANY_SOURCE, 1000, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            comm_time += MPI_Wtime() - t;
            global_lastA = buf[0];
            global_lastB = buf[1];
            global_lastC = buf[2];
        }
    }
    else{
        for(long i = 0; i < local_n; i++){
            long global_i = start_row + i;
            if(global_i < 10){
                int buf[30];
                for(int j = 0; j < 10; j++){
                    buf[j] = local_firstA[global_i][j];
                }
                for(int j = 0; j < 10; j++){
                    buf[10 + j] = local_firstB[global_i][j];
                }
                for(int j = 0; j < 10; j++){
                    buf[20 + j] = local_firstC[global_i][j];
                }
                double t = MPI_Wtime();
                MPI_Send(buf, 30, MPI_INT, 0, global_i, MPI_COMM_WORLD);
                comm_time += MPI_Wtime() - t;
            }
            if(has_last == 1){
                int buf[3] = {local_lastA, local_lastB, local_lastC};
                double t = MPI_Wtime();
                MPI_Send(buf, 3, MPI_INT, 0, 1000, MPI_COMM_WORLD);
                comm_time += MPI_Wtime() - t;
            }
        }
    }
    double max_comp, max_comm, max_total;
    MPI_Reduce(&comp_time, &max_comp, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_io, &max_comm, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_total, &max_total, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    if(rank == 0){
        printf("First 10x10 of A:\n");
        for(int i = 0; i < 10; i++){
            for(int j = 0; j < 10; j++){
                printf("%d ", global_firstA[i][j]);
            }
            printf("\n");
        }
        printf("First 10x10 of B:\n");
        for(int i = 0; i < 10; i++){
            for(int j = 0; j < 10; j++){
                printf("%d ", global_firstB[i][j]);
            }
            printf("\n");
        }
        printf("First 10x10 of C:\n");
        for(int i = 0; i < 10; i++){
            for(int j = 0; j < 10; j++){
                printf("%d ", global_firstC[i][j]);
            }
            printf("\n");
        }
        printf("Last element of A: %d\n", global_lastA);
        printf("Last element of B: %d\n", global_lastB);
        printf("Last element of C: %d\n", global_lastC);
        printf("I/O time: %lf\n", max_comm);
        printf("CPU computation time: %lf\n", max_comp);
        printf("Total simulation time: %lf\n", max_total);
    }
    MPI_Finalize();
    return 0;
}
