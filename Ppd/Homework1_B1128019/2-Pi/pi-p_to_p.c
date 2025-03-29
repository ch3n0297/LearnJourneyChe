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
    double comm_time = 0.0;
    if(rank != 0){
        double t = MPI_Wtime();
        MPI_Send(&local_count,1,MPI_LONG,0,0,MPI_COMM_WORLD);
        comm_time += MPI_Wtime()-t;
    } else {
        long total_count = local_count;
        for(int i=1;i<size;i++){
            long temp;
            double t = MPI_Wtime();
            MPI_Recv(&temp,1,MPI_LONG,i,0,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            comm_time += MPI_Wtime()-t;
            total_count += temp;
        }
        double pi = 4.0*(double)total_count/N;
        double max_cpu = local_cpu_time, max_io = local_io, max_total = local_total;
        for(int i=1;i<size;i++){
            double t_cpu, t_io, t_total;
            double t = MPI_Wtime();
            MPI_Recv(&t_cpu,1,MPI_DOUBLE,i,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            comm_time += MPI_Wtime()-t;
            t = MPI_Wtime();
            MPI_Recv(&t_io,1,MPI_DOUBLE,i,2,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            comm_time += MPI_Wtime()-t;
            t = MPI_Wtime();
            MPI_Recv(&t_total,1,MPI_DOUBLE,i,3,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            comm_time += MPI_Wtime()-t;
            if(t_cpu>max_cpu) max_cpu = t_cpu;
            if(t_io>max_io) max_io = t_io;
            if(t_total>max_total) max_total = t_total;
        }
        printf("Estimated Pi: %.3f\n",pi);
        printf("I/O time: %lf\n",max_io);
        printf("CPU time: %lf\n",max_cpu);
        printf("Total simulation time: %lf\n",max_total);
        printf("Communication time: %lf\n",comm_time);
    }
    if(rank != 0){
        MPI_Send(&local_cpu_time,1,MPI_DOUBLE,0,1,MPI_COMM_WORLD);
        MPI_Send(&local_io,1,MPI_DOUBLE,0,2,MPI_COMM_WORLD);
        MPI_Send(&local_total,1,MPI_DOUBLE,0,3,MPI_COMM_WORLD);
    }
    MPI_Finalize();
    return 0;
}

