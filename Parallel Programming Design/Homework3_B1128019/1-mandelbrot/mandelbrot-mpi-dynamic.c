#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <mpi.h>

#define MAX_ITER 1000                 /* 可自行調高以凸顯發散差異 */
#define TAG_WORK 1
#define TAG_STOP 2

/* ---------- 彩色映射（同 Serial） ---------- */
static inline void rgb_color(double t, int *r, int *g, int *b) {
    t = pow(t, 0.4);
    double red   = 9  * (1 - t) * t * t * t;
    double green = 15 * (1 - t) * (1 - t) * t * t;
    double blue  = 8.5* (1 - t) * (1 - t) * (1 - t) * t;
    *r = (int)fmin(255, red   * 255);
    *g = (int)fmin(255, green * 255);
    *b = (int)fmin(255, blue  * 255);
}

/* ---------- 判斷 |Z_{k+1}| > 2 ---------- */
static inline int mandelbrot(double cr, double ci) {
    double zr = 0.0, zi = 0.0;
    int iter = 0;
    while (zr*zr + zi*zi <= 4.0 && iter < MAX_ITER) {
        double tmp = zr*zr - zi*zi + cr;
        zi = 2.0*zr*zi + ci;
        zr = tmp;
        ++iter;
    }
    return iter;
}

/* ---------- PPM 輸出 (僅 rank 0) ---------- */
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

    /* ---------- 解析命令列參數 ---------- */
    if (argc != 5) {
        if (rank == 0)
            fprintf(stderr,
                "Usage: %s <width> <height> <x_points> <y_points>\n", argv[0]);
        MPI_Finalize();  return 1;
    }
    const int width   = atoi(argv[1]);
    const int height  = atoi(argv[2]);
    const int x_points = atoi(argv[3]);
    const int y_points = atoi(argv[4]);
    if (width<=0 || height<=0 || x_points<=0 || y_points<=0) {
        if (rank==0) fprintf(stderr, "All parameters must be positive.\n");
        MPI_Finalize();  return 1;
    }
    if (rank==0 && (width!=x_points || height!=y_points))
        fprintf(stderr,
          "Warning: width/height 與 x_points/y_points 不一致，計算仍以 width/height 為準。\n");

    /* ---------- 計時器 ---------- */
    double t_total_start = MPI_Wtime();
    double t_comp_start  = MPI_Wtime();

    /* ---------- 常數 ---------- */
    const double x_min=-2.0, x_max=1.0;
    const double y_min=-1.5, y_max=1.5;

    /********************* Rank 0：工作池排程器 *************************/
    if (rank == 0) {
        unsigned char *image = malloc((size_t)width * height * 3);
        if (!image) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD,1); }

        int next_row = 0;                  /* 下一行尚未派發的 row index */
        int active_workers = size - 1;

        /* 初始派工：先給每個 worker 一行 */
        for (int w = 1; w < size && next_row < height; ++w, ++next_row)
            MPI_Send(&next_row, 1, MPI_INT, w, TAG_WORK, MPI_COMM_WORLD);

        /* 主排程迴圈 */
        while (active_workers > 0) {
            int row_idx;                   /* 先收 row index 再收像素 */
            MPI_Status st;
            MPI_Recv(&row_idx, 1, MPI_INT, MPI_ANY_SOURCE,
                     MPI_ANY_TAG, MPI_COMM_WORLD, &st);
            int worker = st.MPI_SOURCE;

            /* 接收該行像素資料 */
            MPI_Recv(image + (size_t)row_idx * width * 3,
                     width*3, MPI_UNSIGNED_CHAR,
                     worker, TAG_WORK, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            /* 指派新工作或送終止訊息 */
            if (next_row < height) {
                MPI_Send(&next_row, 1, MPI_INT, worker, TAG_WORK, MPI_COMM_WORLD);
                ++next_row;
            } else {
                MPI_Send(&next_row, 1, MPI_INT, worker, TAG_STOP, MPI_COMM_WORLD);
                --active_workers;
            }
        }

        double t_comp_end = MPI_Wtime();          /* rank 0 不計算像素，comp≈0 */
        double io_time = 0.0;
        /* ---------- 輸出檔案 ---------- */
        double t_io_start = MPI_Wtime();
        write_ppm_rank0("mandelbrot_rgb(mpi-dynamic).ppm", width, height, image);
        double t_io_end   = MPI_Wtime();
        io_time = t_io_end - t_io_start;

        double total_time  = MPI_Wtime() - t_total_start;

        /* 收集各 worker 最大 compute 時間 */
        double comp_time_dummy = 0.0;
        double comp_time_max   = 0.0;
        MPI_Reduce(&comp_time_dummy, &comp_time_max, 1,
                   MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

        double comm_time = total_time - comp_time_max - io_time;
        if (comm_time < 0) comm_time = 0;     /* 數值保護 */

        fprintf(stderr,
          "[MPI-Dynamic] compute=%.6f s (max-rank), comm=%.6f s, IO=%.6f s, total=%.6f s\n",
          comp_time_max, comm_time, io_time, total_time);
        fprintf(stderr,
          "Image saved to mandelbrot_rgb(mpi-dynamic).ppm  (use convert to PNG if needed)\n");

        free(image);
        MPI_Finalize();
        return 0;
    }

    /*********************** Worker ranks *****************************/
    /* Worker 計算單行像素後回傳 */
    unsigned char *rowbuf = malloc(width * 3);
    if (!rowbuf) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD,1); }

    double my_comp_time = 0.0;
    while (1) {
        int row_idx;
        MPI_Status st;
        MPI_Recv(&row_idx, 1, MPI_INT, 0 /*rank0*/,
                 MPI_ANY_TAG, MPI_COMM_WORLD, &st);

        if (st.MPI_TAG == TAG_STOP) break;        /* 收到停止訊號 */

        double t0 = MPI_Wtime();                  /* 行計算開始 */

        double ci = y_max - row_idx * (y_max - y_min) / height;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);
            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t = (double)iter / MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;
            rowbuf[x*3]   = (unsigned char)r;
            rowbuf[x*3+1] = (unsigned char)g;
            rowbuf[x*3+2] = (unsigned char)b;
        }

        double t1 = MPI_Wtime();
        my_comp_time += (t1 - t0);

        /* 先送 row index，再送像素資料 */
        MPI_Send(&row_idx, 1, MPI_INT, 0, TAG_WORK, MPI_COMM_WORLD);
        MPI_Send(rowbuf, width*3, MPI_UNSIGNED_CHAR, 0, TAG_WORK, MPI_COMM_WORLD);
    }

    /* 將自己累積的 compute time 取 max 到 rank 0 */
    MPI_Reduce(&my_comp_time, NULL, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    free(rowbuf);
    MPI_Finalize();
    return 0;
}
