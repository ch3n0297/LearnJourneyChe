/*
 * sort_verifier_serial_hpc.c
 *
 * 針對大型 HPC 環境優化的 Serial 排序正確性驗證程式
 * 
 * 編譯 (gcc):
 *   gcc -O3 -march=native -std=c11 -o sort_verify sort_verifier_serial_hpc.c
 *
 * 用法範例:
 *   ./sort_verify -i large_input.bin -k 2048 -b 4194304 -v -t
 *
 * 參數說明:
 *   -i <path>    : (必填) 輸入檔案路徑，格式請參考下方說明
 *   -k <size>    : 切分錯位區段時的最大長度 K (uint64_t)，預設 1024
 *   -b <bytes>   : 讀檔緩衝區大小 (Bytes)，預設 1<<20 (1 MiB)
 *   -v           : 開啟詳細模式 (verbose)，印出更多錯位前後內容
 *   -t           : 印出程式總執行時間資訊
 *   -h           : 顯示說明
 *
 * 輸入檔案格式 (binary 或純文字皆可，但需自行調整讀取方式):
 *   - 若為純文字 (text mode):
 *       第一行：N (uint64_t)
 *       之後共 N 個 64-bit 整數，以空白或換行分隔
 *   - 若為二進位 (binary mode):
 *       直接存放 N 個 uint64_t（不含前置 N），請自行轉檔或改程式讀取邏輯
 */

#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>      // getopt
#include <time.h>        // clock_gettime
#include <sys/stat.h>    // stat for file size

// 預設參數值—較為精簡，降低預設資源占用
#define DEFAULT_K            512ULL
#define DEFAULT_BUFFER_BYTES (1ULL << 19)    // 512 KiB

// 全域變數，看要不要在程式內共用（這裡只是示範）
static uint64_t K = DEFAULT_K;
static size_t   BUFFER_SIZE = DEFAULT_BUFFER_BYTES;
static int      VERBOSE = 0;
static int      SHOW_TIME = 0;

// 計時輔助：取得目前時間 (秒.奈秒)
static double now_sec()
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

// 顯示使用說明
static void usage(const char *prog)
{
    fprintf(stderr,
        "Usage: %s -i <input-file> [options]\n"
        "  -i <path>    : (必填) 輸入檔案路徑\n"
        "  -k <size>    : 錯位區段最大長度 K (uint64_t)，預設 %" PRIu64 "\n"
        "  -b <bytes>   : 讀檔緩衝區大小 (Bytes)，預設 %zu\n"
        "  -v           : 詳細模式 (verbose)\n"
        "  -t           : 顯示程式執行時間\n"
        "  -h           : 顯示此說明\n\n"
        "輸入檔案格式說明 (範例採純文字模式，若為二進位請自行調整讀取):\n"
        "  [第一行] N (uint64_t)\n"
        "  [之後 N 個值] 64-bit signed integers，以空白或換行分隔。\n\n"
        "Example:\n"
        "  %s -i large_input.txt -k 2048 -b 4194304 -v -t\n",
        prog, DEFAULT_K, (size_t)DEFAULT_BUFFER_BYTES, prog);
}

// 從指定檔案路徑讀取所有 uint64_t，並回傳指標與元素個數
// 這裡先實作純文字模式 (text mode)；若要改成二進位請自行修改 fread 部分
static int load_array_from_text(const char *path, uint64_t **out_arr, uint64_t *out_n)
{
    FILE *fp = fopen(path, "r");
    if (!fp) {
        fprintf(stderr, "Error opening file '%s': %s\n", path, strerror(errno));
        return -1;
    }

    // 讀取 N
    uint64_t N;
    if (fscanf(fp, "%" SCNu64, &N) != 1) {
        fprintf(stderr, "Failed to read N from '%s'\n", path);
        fclose(fp);
        return -1;
    }

    // 配置對齊記憶體 (64-byte 對齊)
    uint64_t *A = NULL;
    int ret = posix_memalign((void **)&A, 64, sizeof(uint64_t) * N);
    if (ret != 0 || A == NULL) {
        fprintf(stderr, "Memory allocation failed for N=%" PRIu64 "\n", N);
        fclose(fp);
        return -1;
    }

    // 逐一讀取 N 個 64 位整數
    for (uint64_t i = 0; i < N; i++) {
        if (fscanf(fp, "%" SCNd64, (int64_t *)&A[i]) != 1) {
            fprintf(stderr, "Failed to read element %" PRIu64 " from '%s'\n", i, path);
            free(A);
            fclose(fp);
            return -1;
        }
    }
    fclose(fp);

    *out_arr = A;
    *out_n   = N;
    return 0;
}

// 主程式
int main(int argc, char *argv[])
{
    const char *input_path = NULL;
    int opt;

    // 解析命令列參數
    while ((opt = getopt(argc, argv, "i:k:b:vth")) != -1) {
        switch (opt) {
            case 'i':
                input_path = optarg;
                break;
            case 'k': {
                uint64_t tmp = strtoull(optarg, NULL, 10);
                if (tmp == 0) {
                    fprintf(stderr, "Invalid K: %s\n", optarg);
                    return EXIT_FAILURE;
                }
                K = tmp;
                break;
            }
            case 'b': {
                uint64_t tmp = strtoull(optarg, NULL, 10);
                if (tmp == 0) {
                    fprintf(stderr, "Invalid buffer size: %s\n", optarg);
                    return EXIT_FAILURE;
                }
                BUFFER_SIZE = (size_t)tmp;
                break;
            }
            case 'v':
                VERBOSE = 1;
                break;
            case 't':
                SHOW_TIME = 1;
                break;
            case 'h':
                usage(argv[0]);
                return EXIT_SUCCESS;
            default:
                usage(argv[0]);
                return EXIT_FAILURE;
        }
    }

    if (!input_path) {
        fprintf(stderr, "Error: 必須指定輸入檔案路徑 (-i)\n\n");
        usage(argv[0]);
        return EXIT_FAILURE;
    }

    // 計時開始
    double t_start = now_sec();

    // 讀取輸入陣列
    uint64_t *A = NULL, N = 0;
    if (load_array_from_text(input_path, &A, &N) != 0) {
        return EXIT_FAILURE;
    }
    if (VERBOSE) {
        fprintf(stderr, "[INFO] 成功載入 N = %" PRIu64 " 個元素\n", N);
    }

    // 主掃描：尋找第一個 A[i] > A[i+1]
    uint64_t inv_idx = UINT64_MAX;
    for (uint64_t i = 0; i < N - 1; i++) {
        if (A[i] > A[i + 1]) {
            inv_idx = i;
            break;
        }
    }

    if (inv_idx == UINT64_MAX) {
        // 全部都排序
        printf("Array is sorted. PASS.\n");
        if (SHOW_TIME) {
            double t_end = now_sec();
            printf("[TIME] total elapsed = %.6f sec\n", t_end - t_start);
        }
        free(A);
        return EXIT_SUCCESS;
    }

    // 找到第一處錯位
    printf("Array is NOT sorted.\n");
    printf("First adjacent inversion at index inv_idx = %" PRIu64
           " (A[%" PRIu64 "] = %" PRIu64 ", A[%" PRIu64 "] = %" PRIu64 ").\n",
           inv_idx, inv_idx, A[inv_idx], inv_idx + 1, A[inv_idx + 1]);

    // 向左擴張 l
    uint64_t l = inv_idx;
    while (l > 0 && A[l - 1] > A[l]) {
        l--;
    }

    // 向右擴張 r
    uint64_t r = inv_idx + 1;
    while (r < N - 1 && A[r] > A[r + 1]) {
        r++;
    }

    uint64_t seg_len = r - l + 1;
    printf("Unsorted segment = [%" PRIu64 ", %" PRIu64 "], length = %" PRIu64 ".\n",
           l, r, seg_len);

    if (seg_len > K) {
        printf("WARNING: segment length %" PRIu64 " > K (%" PRIu64 ").\n"
               "Consider splitting into smaller chunks of length <= K for後續處理。\n",
               seg_len, K);
    }

    // 如果是詳細模式，可印出錯位範圍前後兩個元素做檢查
    if (VERBOSE) {
        uint64_t left_print_start  = (l >= 2 ? l - 2 : 0);
        uint64_t left_print_end    = (l + 2 < N ? l + 2 : N - 1);
        uint64_t right_print_start = (r >= 2 ? r - 2 : 0);
        uint64_t right_print_end   = (r + 2 < N ? r + 2 : N - 1);

        printf("[VERBOSE] Around l (index %" PRIu64 "): ", l);
        for (uint64_t i = left_print_start; i <= left_print_end; i++) {
            printf("%" PRIu64 " ", A[i]);
        }
        printf("\n");

        printf("[VERBOSE] Around r (index %" PRIu64 "): ", r);
        for (uint64_t i = right_print_start; i <= right_print_end; i++) {
            printf("%" PRIu64 " ", A[i]);
        }
        printf("\n");
    }

    // 完成
    if (SHOW_TIME) {
        double t_end = now_sec();
        printf("[TIME] total elapsed = %.6f sec\n", t_end - t_start);
    }

    free(A);
    return EXIT_SUCCESS;
}
