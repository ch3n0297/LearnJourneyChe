#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define N 100000000
int main(int argc, char **argv){
    MPI_Init(&argc,&argv);
    int rank,size;
    MPI_Comm_rank(MPI_COMM_WORLD,&rank);
    MPI_Comm_size(MPI_COMM_WORLD,&size);
    srand(time(NULL)+rank);
    double start_total = MPI_Wtime();
    long base = N/size;
    long rem = N%size;
    long local_N = (rank < rem) ? base+1 : base;
    double start_cpu = MPI_Wtime();
    long local_count = 0;
    for(long i=0;i<local_N;i++){
        double x = (double)rand()/RAND_MAX*2.0 - 1.0;
        double y = (double)rand()/RAND_MAX*2.0 - 1.0;
        if(x*x+y*y<=1.0) local_count++;
    }
    double end_cpu = MPI_Wtime();
    double local_cpu_time = end_cpu - start_cpu;
    double local_total = MPI_Wtime() - start_total;
    double local_io = local_total - local_cpu_time;
    double comm_time = 0.0, t;
    long total_count = 0;
    t = MPI_Wtime();
    MPI_Reduce(&local_count,&total_count,1,MPI_LONG,MPI_SUM,0,MPI_COMM_WORLD);
    comm_time += MPI_Wtime()-t;
    double max_cpu_time = 0.0, max_io_time = 0.0, max_total_time = 0.0;
    t = MPI_Wtime();
    MPI_Reduce(&local_cpu_time,&max_cpu_time,1,MPI_DOUBLE,MPI_MAX,0,MPI_COMM_WORLD);
    comm_time += MPI_Wtime()-t;
    t = MPI_Wtime();
    MPI_Reduce(&local_io,&max_io_time,1,MPI_DOUBLE,MPI_MAX,0,MPI_COMM_WORLD);
    comm_time += MPI_Wtime()-t;
    t = MPI_Wtime();
    MPI_Reduce(&local_total,&max_total_time,1,MPI_DOUBLE,MPI_MAX,0,MPI_COMM_WORLD);
    comm_time += MPI_Wtime()-t;
    if(rank==0){
        double pi = 4.0*(double)total_count/N;
        printf("Estimated Pi: %.3f\n",pi);
        printf("I/O time: %lf\n",max_io_time);
        printf("CPU time: %lf\n",max_cpu_time);
        printf("Total simulation time: %lf\n",max_total_time);
        printf("Communication time: %lf\n",comm_time);
    }
    MPI_Finalize();
    return 0;
}

