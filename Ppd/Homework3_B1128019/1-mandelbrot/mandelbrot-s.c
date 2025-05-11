#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define MAX_ITER 1000

/* ---------- 彩色映射 ---------- */
void rgb_color(double t, int *r, int *g, int *b) {
    t = pow(t, 0.4);                         /* nonlinear brightness */
    double red   = 9  * (1 - t) * t * t * t;
    double green = 15 * (1 - t) * (1 - t) * t * t;
    double blue  = 8.5* (1 - t) * (1 - t) * (1 - t) * t;
    *r = (int)fmin(255, red   * 255);
    *g = (int)fmin(255, green * 255);
    *b = (int)fmin(255, blue  * 255);
}

/* ---------- 發散/收斂判斷 ---------- */
int mandelbrot(double cr, double ci) {
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

/* ---------- PPM (P3) 輸出 ---------- */
void write_ppm(const char *fname, int w, int h, const unsigned char *img) {
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

static inline double sec(const struct timespec *beg,
                         const struct timespec *end)
{
    return (end->tv_sec - beg->tv_sec) +
           (end->tv_nsec - beg->tv_nsec) / 1e9;
}

int main(int argc, char **argv) {
    /* ---------- 參數 ---------- */
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <width> <height>\n", argv[0]);
        return 1;
    }
    const int width  = atoi(argv[1]);
    const int height = atoi(argv[2]);
    if (width <= 0 || height <= 0) {
        fprintf(stderr, "Error: width and height must be positive.\n");
        return 1;
    }

    /* ---------- 影像緩衝 ---------- */
    unsigned char *image = malloc((size_t)width * height * 3);
    if (!image) { perror("malloc"); return 1; }

    /* ---------- 時間變數 ---------- */
    struct timespec total_start, total_end;
    struct timespec comp_start,  comp_end;
    clock_gettime(CLOCK_MONOTONIC, &total_start);
    clock_gettime(CLOCK_MONOTONIC, &comp_start);

    /* ---------- 計算 Mandelbrot ---------- */
    const double x_min=-2.0, x_max=1.0;
    const double y_min=-1.5, y_max=1.5;
    for (int y = 0; y < height; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = image + (size_t)y * width * 3;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);
            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t=(double)iter/MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;
            row[x*3]   = (unsigned char)r;
            row[x*3+1] = (unsigned char)g;
            row[x*3+2] = (unsigned char)b;
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &comp_end);

    /* ---------- 輸出圖檔 ---------- */
    write_ppm("mandelbrot_rgb(serial).ppm", width, height, image);

    clock_gettime(CLOCK_MONOTONIC, &total_end);

    /* ---------- 時間統計 ---------- */
    double compute_time = sec(&comp_start,  &comp_end);
    double total_time   = sec(&total_start, &total_end);
    double io_time      = total_time - compute_time;   /* 純 Serial → comm=0 */

    fprintf(stderr,
        "[Serial] compute=%.6f s, IO=%.6f s, comm=0.000000 s, total=%.6f s\n",
        compute_time, io_time, total_time);

    free(image);
    return 0;
}
