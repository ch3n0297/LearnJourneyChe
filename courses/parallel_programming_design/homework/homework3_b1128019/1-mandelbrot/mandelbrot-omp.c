#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <omp.h>

#define MAX_ITER 1000           /* 可自行調高以觀察發散差異 */

/* ---------- 彩色映射 ---------- */
static inline void rgb_color(double t, int *r, int *g, int *b) {
    t = pow(t, 0.4);            /* nonlinear brightness */
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
    while (zr*zr + zi*zi <= 4.0 && iter < MAX_ITER) { /* |Z_{k+1}| > 2 ? */
        double tmp = zr*zr - zi*zi + cr;
        zi = 2.0*zr*zi + ci;
        zr = tmp;
        ++iter;
    }
    return iter;
}

/* ---------- PPM (P3) 輸出 ---------- */
static void write_ppm(const char *fname, int w, int h,
                      const unsigned char *img)
{
    FILE *fp = fopen(fname, "w");
    if (!fp) { perror("fopen"); exit(1); }
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
    /* ---------- 解析命令列 ---------- */
    if (argc != 5) {
        fprintf(stderr,
            "Usage: %s <width> <height> <x_points> <y_points>\n", argv[0]);
        return 1;
    }
    const int width   = atoi(argv[1]);
    const int height  = atoi(argv[2]);
    const int x_points = atoi(argv[3]);
    const int y_points = atoi(argv[4]);
    if (width<=0 || height<=0 || x_points<=0 || y_points<=0) {
        fprintf(stderr, "All parameters must be positive.\n");
        return 1;
    }
    if ((width!=x_points || height!=y_points))
        fprintf(stderr,
            "Warning: width/height 與 x_points/y_points 不一致，仍以 width/height 計算。\n");

    /* ---------- 配置影像緩衝 ---------- */
    unsigned char *image = malloc((size_t)width * height * 3);
    if (!image) { perror("malloc"); return 1; }

    /* ---------- 常數 ---------- */
    const double x_min=-2.0, x_max=1.0;
    const double y_min=-1.5, y_max=1.5;

    /* ---------- 計時 ---------- */
    double t_total_start = omp_get_wtime();
    double t_comp_start  = omp_get_wtime();

    /* ---------- OpenMP 平行計算 ---------- */
    /* 以行 (row) 為工作單位，動態排程避免負載不均 */
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y < height; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = image + (size_t)y * width * 3;
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

    double t_comp_end = omp_get_wtime();

    /* ---------- 寫檔 ---------- */
    double t_io_start = omp_get_wtime();
    write_ppm("mandelbrot_rgb(omp).ppm", width, height, image);
    double t_io_end   = omp_get_wtime();

    double total_time   = omp_get_wtime() - t_total_start;
    double compute_time = t_comp_end - t_comp_start;
    double io_time      = t_io_end   - t_io_start;
    double comm_time    = 0.0;      /* OpenMP 共記憶體 → 通訊時間視為 0 */

    fprintf(stderr,
        "[OpenMP] compute=%.6f s, comm=%.6f s, IO=%.6f s, total=%.6f s\n",
        compute_time, comm_time, io_time, total_time);
    fprintf(stderr,
        "Image saved to mandelbrot_rgb(omp).ppm  (use convert to PNG if needed)\n");

    free(image);
    return 0;
}
