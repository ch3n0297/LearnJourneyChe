#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <mpi.h>

#define MAX_ITER 1000                       /* 可自行調高顯示更多漸層 */

/* ---------- 彩色映射 (同 serial) ---------- */
static inline void rgb_color(double t, int *r, int *g, int *b) {
    t = pow(t, 0.4);                       /* nonlinear brightness */
    double red   = 9  * (1 - t) * t * t * t;
    double green = 15 * (1 - t) * (1 - t) * t * t;
    double blue  = 8.5* (1 - t) * (1 - t) * (1 - t) * t;
    *r = (int)fmin(255, red   * 255);
    *g = (int)fmin(255, green * 255);
    *b = (int)fmin(255, blue  * 255);
}

/* ---------- 發散/收斂判斷 ---------- */
static inline int mandelbrot(double cr, double ci) {
    double zr = 0.0, zi = 0.0;
    int iter = 0;
    while (zr*zr + zi*zi <= 4.0 && iter < MAX_ITER) {  /* |Z_{k+1}| > 2? */
        double tmp = zr*zr - zi*zi + cr;
        zi = 2.0*zr*zi + ci;
        zr = tmp;
        ++iter;
    }
    return iter;
}

/* ---------- PPM(P3) 輸出 (只在 rank 0 呼叫) ---------- */
static void write_ppm_rank0(const char *fname,
                            int w, int h, const unsigned char *img)
{
    FILE *fp = fopen(fname, "w");
    if (!fp) { perror("fopen"); MPI_Abort(MPI_COMM_WORLD, 1); }
    fprintf(fp, "P3\n%d %d\n255\n", w, h);
    for (int y = 0; y < h; ++y) {
        const unsigned char *row = img + (size_t)y * w * 3;
        for (int x = 0; x < w; ++x)
            fprintf(fp, "%d %d %d ",
                    row[x*3], row[x*3+1], row[x*3+2]);
        fputc('\n', fp);
    }
    fclose(fp);
}

int main(int argc, char **argv)
{
    /* ---------- MPI 初始化 ---------- */
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    /* ---------- 處理輸入參數 ---------- */
    if (argc != 5) {
        if (rank == 0)
            fprintf(stderr,
                "Usage: %s <width> <height> <x_points> <y_points>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }
    const int width   = atoi(argv[1]);
    const int height  = atoi(argv[2]);
    const int x_points = atoi(argv[3]);
    const int y_points = atoi(argv[4]);

    if (width<=0 || height<=0 || x_points<=0 || y_points<=0) {
        if (rank==0) fprintf(stderr, "All parameters must be positive.\n");
        MPI_Finalize(); return 1;
    }
    /* 建議 width==x_points, height==y_points；若不一致，僅警告 */
    if (rank==0 && (width!=x_points || height!=y_points))
        fprintf(stderr,
          "Warning: width/height 與 x_points/y_points 不一致，程式將以 width/height 為準計算。\n");

    /* ---------- 分配各 rank 行數 (static) ---------- */
    int rows_per   = (height + size - 1) / size;     /* ceiling */
    int row_start  = rank * rows_per;
    int row_end    = ((rank+1)*rows_per > height) ? height : (rank+1)*rows_per;
    int my_rows    = row_end - row_start;

    unsigned char *subimg = malloc((size_t)my_rows * width * 3);
    if (!subimg) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD, 1); }

    /* ---------- 時間量測 ---------- */
    double t_total_start = MPI_Wtime();
    double t_comp_start  = MPI_Wtime();

    /* ---------- Mandelbrot 計算 ---------- */
    const double x_min=-2.0, x_max=1.0;
    const double y_min=-1.5, y_max=1.5;

    for (int y = row_start; y < row_end; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = subimg + (size_t)(y-row_start) * width * 3;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);

            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t = (double)iter / MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;

            row[x*3]   = (unsigned char)r;
            row[x*3+1] = (unsigned char)g;
            row[x*3+2] = (unsigned char)b;
        }
    }

    double t_comp_end = MPI_Wtime();
    double comp_time  = t_comp_end - t_comp_start;

    /* ---------- 蒐集影像到 rank 0 ---------- */
    int *recvcounts = NULL, *displs = NULL;
    if (rank == 0) {
        recvcounts = malloc(size * sizeof(int));
        displs     = malloc(size * sizeof(int));
        for (int i = 0; i < size; ++i) {
            int s = i * rows_per;
            int e = ((i+1)*rows_per > height) ? height : (i+1)*rows_per;
            recvcounts[i] = (e - s) * width * 3;
            displs[i]     = s * width * 3;
        }
    }

    unsigned char *fullimg = NULL;
    if (rank == 0)
        fullimg = malloc((size_t)height * width * 3);

    MPI_Gatherv(subimg, my_rows*width*3, MPI_UNSIGNED_CHAR,
                fullimg, recvcounts, displs, MPI_UNSIGNED_CHAR,
                0, MPI_COMM_WORLD);

    /* ---------- rank 0 寫檔 ---------- */
    double io_time = 0.0;
    if (rank == 0) {
        double t_io_start = MPI_Wtime();
        write_ppm_rank0("mandelbrot_rgb(mpi-static).ppm", width, height, fullimg);
        double t_io_end   = MPI_Wtime();
        io_time = t_io_end - t_io_start;
    }

    double t_total_end = MPI_Wtime();
    double total_time  = t_total_end - t_total_start;

    /* ---------- 收集最大計算時間 ---------- */
    double comp_time_max = 0.0;
    MPI_Reduce(&comp_time, &comp_time_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    /* ---------- rank 0 輸出統計 ---------- */
    if (rank == 0) {
        /* communication_time = total - compute_max - io */
        double comm_time = total_time - comp_time_max - io_time;
        if (comm_time < 0) comm_time = 0;   /* 數值誤差保護 */

        fprintf(stderr,
          "[MPI-Static] compute=%.6f s (max-rank), comm=%.6f s, IO=%.6f s, total=%.6f s\n",
          comp_time_max, comm_time, io_time, total_time);
        fprintf(stderr,
          "Image saved to mandelbrot_rgb(mpi-static).ppm  (use convert to PNG if needed)\n");

        free(fullimg);
        free(recvcounts);
        free(displs);
    }

    free(subimg);
    MPI_Finalize();
    return 0;
}
