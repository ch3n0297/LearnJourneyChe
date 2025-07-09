#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define N 100000000
int main(int argc, char **argv){
    MPI_Init(&argc,&argv);
    srand(time(NULL));
    double start_total = MPI_Wtime();
    long count = 0;
    double start_cpu = MPI_Wtime();
    for(long i=0;i<N;i++){
        double x = (double)rand()/RAND_MAX*2.0 - 1.0;
        double y = (double)rand()/RAND_MAX*2.0 - 1.0;
        if(x*x+y*y<=1.0) count++;
    }
    double end_cpu = MPI_Wtime();
    double pi = 4.0*(double)count/N;
    double end_total = MPI_Wtime();
    double cpu_time = end_cpu - start_cpu;
    double io_time = (end_total - start_total) - cpu_time;
    printf("Estimated Pi: %.3f\n",pi);
    printf("I/O time: %lf\n",io_time);
    printf("CPU time: %lf\n",cpu_time);
    printf("Total simulation time: %lf\n",end_total-start_total);
    MPI_Finalize();
    return 0;
}

