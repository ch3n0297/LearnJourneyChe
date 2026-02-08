#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <stdbool.h>

#define N 50000  /* Number of random doubles to generate */

/* Insertion sort implementation for double arrays */
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

/* Simple correctness check */
static bool is_sorted(const double *arr, int n) {
    for (int i = 1; i < n; ++i) {
        if (arr[i] < arr[i - 1]) {
            return false;
        }
    }
    return true;
}

int main(void) {
    /* Allocate memory for the dataset */
    double *data = (double *)malloc(N * sizeof(double));
    if (!data) {
        fprintf(stderr, "Memory allocation failed\n");
        return EXIT_FAILURE;
    }

    /* Generate random numbers rounded to 2 decimal places */
    srand((unsigned int)time(NULL));
    for (int i = 0; i < N; ++i) {
        double r = (double)rand() / RAND_MAX;   /* 0.0–1.0 */
        r = round(r * 10000.0) / 100.0;         /* 0.00–100.00 with 2 decimals */
        data[i] = r;
    }

    /* Measure CPU time for the sorting phase */
    clock_t start = clock();
    insertion_sort(data, N);
    clock_t end   = clock();

    /* Verify sorting correctness (optional for release) */
    if (!is_sorted(data, N)) {
        fprintf(stderr, "Sort verification failed!\n");
        free(data);
        return EXIT_FAILURE;
    }

    /* Print the first 10 sorted values for sanity check */
    printf("First 10 sorted numbers:\n");
    for (int i = 0; i < 10; ++i) {
        printf("%.2f ", data[i]);
    }
    printf("\n");

    /* Report timing */
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    printf("CPU sorting time: %.6f seconds\n", elapsed);

    free(data);
    return EXIT_SUCCESS;
}
