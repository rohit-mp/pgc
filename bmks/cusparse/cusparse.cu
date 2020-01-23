#include <stdio.h>
#include <stdlib.h>
#include "cusparse.h"
#include "cuda.h"
#include <getopt.h>

#include "gg.h"
#include "Timer.h"

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    cusparseStatus_t status = (func);                                          \
    if (status != CUSPARSE_STATUS_SUCCESS) {                                   \
        printf("CUSPARSE API failed with error (%d) at line %d\n",             \
                status, __LINE__);                                              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

char *INPUT, *OUTPUT;
int QUIET = 0;
int CUDA_DEVICE = 0;
int DIS_NCOLORS = 0;

void usage(int argc, char *argv[]) {
    fprintf(stderr, "usage: %s [-q] [-g gpunum] [-o output-file] [-c output number of colors] graph-file\n", argv[0]);
}

void parse_args(int argc, char *argv[]) {
    char opts[] = "g:qo:c";
    int len = strlen(opts)+1;
    int c;

    while((c = getopt(argc, argv, opts)) != -1) {
        switch(c) {
            case 'q':
                QUIET = 1;
                break;
            case 'o':
                OUTPUT = optarg;
                break;
            case 'g':
                char *end;
                errno = 0;
                CUDA_DEVICE = strtol(optarg, &end, 10);
                if(errno != 0 || *end != '\0') {
                    fprintf(stderr, "Invalid GPU device '%s'. An integer must be specified.\n", optarg);
                    exit(EXIT_FAILURE);
                }
            case 'c':
                DIS_NCOLORS = 1;
                break;
            case '?':
                usage(argc, argv);
                exit(EXIT_FAILURE);
        }
    }

    if(optind < argc) {
        INPUT = argv[optind];
    }
    else {
        usage(argc, argv);
        exit(EXIT_FAILURE);
    }
}

void output(int m, int *coloring, int ncolors) {
    if(!QUIET) {
        if(DIS_NCOLORS) {
           printf("Chromatic number: %d", ncolors);
        }
        if(OUTPUT) {
            FILE *f;

            if(strcmp(OUTPUT, "-") == 0)
                f = stdout;
            else
                f = fopen(OUTPUT, "w");

            fprintf(f, "%d\n", m); // number of nodes
            for (int i = 0; i < m; i++)
                fprintf(f, "%d %d\n", i, coloring[i]);
        }
    }

}

int main(int argc, char *argv[]) {

    parse_args(argc, argv);

    // CSR matrix variables

    int m, nnz;
    float *val;

    // Load graph and set csr matrix variables

    CSRGraphTy g;
    g.read(INPUT);

    m = g.nnodes;
    nnz = g.nedges;
    val = (float*) malloc(nnz * sizeof(float));
    for(int i = 0; i < nnz; i++) val[i] = 1;

    int *d_rowPtr, *d_colInd;
    float *d_val;

    check_cuda(cudaMalloc((void **)&d_rowPtr, (m + 1) * sizeof(int)));
    check_cuda(cudaMalloc((void **)&d_colInd, nnz * sizeof(int)));
    check_cuda(cudaMalloc((void **)&d_val, nnz * sizeof(int)));

    check_cuda(cudaMemcpy(d_rowPtr, g.row_start, (m + 1) * sizeof(int), cudaMemcpyHostToDevice));
    check_cuda(cudaMemcpy(d_colInd, g.edge_dst, nnz * sizeof(int), cudaMemcpyHostToDevice));
    check_cuda(cudaMemcpy(d_val, val, nnz * sizeof(int), cudaMemcpyHostToDevice));

    // Allocate memory for storing coloring info

    int ncolors = 0, *coloring, *reordering;
    float fraction = 1.0;
    int *d_coloring, *d_reordering;

    coloring = (int *) malloc(m * sizeof(int));
    reordering = (int *) malloc(m * sizeof(int));

    check_cuda(cudaMalloc((void **)&d_coloring, m * sizeof(int))); 
    check_cuda(cudaMalloc((void **)&d_reordering, m * sizeof(int))); 

    // Create handle for cuSPARSE context 

    cusparseHandle_t handle;
    CHECK_CUSPARSE(cusparseCreate(&handle));

    // Create Matrix descriptor and coloring info

    cusparseMatDescr_t descr;
    CHECK_CUSPARSE(cusparseCreateMatDescr(&descr));

    cusparseColorInfo_t info;
    CHECK_CUSPARSE(cusparseCreateColorInfo(&info));

    // Invoking csrcolor (and timing it)

    ggc::Timer k("cusparseScsrsolor");
    k.start();
    CHECK_CUSPARSE(cusparseScsrcolor(handle, m, nnz, descr, d_val, d_rowPtr, d_colInd, &fraction, &ncolors, d_coloring, d_reordering, info));
    cudaDeviceSynchronize();
    k.stop();

    // Copy coloring back to host

    check_cuda(cudaMemcpy(coloring, d_coloring, m * sizeof(int), cudaMemcpyDeviceToHost));
    check_cuda(cudaMemcpy(reordering, d_reordering, m * sizeof(int), cudaMemcpyDeviceToHost));

    // Output

    fprintf(stderr, "Total time: %llu ms\n", k.duration_ms());
    fprintf(stderr, "Total time: %llu ns\n", k.duration());

    output(m, coloring, ncolors);

    // Release memory acquired by descr and info

    CHECK_CUSPARSE(cusparseDestroyColorInfo(info));
    CHECK_CUSPARSE(cusparseDestroyMatDescr(descr));

    // Release CPU side res used by cuSPARSE

    CHECK_CUSPARSE(cusparseDestroy(handle));

    // Free allocated memory

    check_cuda(cudaFree(d_reordering));
    check_cuda(cudaFree(d_coloring));
    check_cuda(cudaFree(d_val));
    check_cuda(cudaFree(d_colInd));
    check_cuda(cudaFree(d_rowPtr));

    free(reordering);
    free(coloring);
    free(val);

    return 0;
}
