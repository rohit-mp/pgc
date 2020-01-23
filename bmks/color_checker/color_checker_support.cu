/* -*- mode: C++ -*- */

#include "gg.h"

const char *prog_opts = "e:";
const char *prog_usage = "[-e number-of-conflicting-nodes-output]";
const char *prog_args_usage = "colors-list-file";

int *COLORS;
int N_NODES, CHROMATIC_NUMBER;
long long ERR = 20; // number of conflicting nodes to display

extern int SKELAPP_RETVAL;

int process_prog_arg(int argc, char *argv[], int arg_start) {
  if(arg_start < argc) {
    FILE *f;

    f = fopen(argv[arg_start], "r");
    
    if(!f) {
      fprintf(stderr, "Unable to open file '%s' (err: %d, %s)\n", argv[arg_start], errno, strerror(errno));
      exit(EXIT_FAILURE);	
    }

    if(fscanf(f, "%d", &N_NODES) != 1) {
      fprintf(stderr, "Unable to read number of nodes\n");
      exit(EXIT_FAILURE);
    }

    assert(N_NODES > 0);

    COLORS = (int *) malloc(N_NODES * sizeof(int));

    printf("Reading list of colors of %d nodes from '%s' ...\n", N_NODES, argv[arg_start]);

    for(int i = 0; i < N_NODES; i++) {
      int node;
      if(fscanf(f, "%d", &node) != 1) {
	fprintf(stderr, "Error while reading node %d\n", i);
	exit(EXIT_FAILURE);
      } 
      if(fscanf(f, "%d", &COLORS[node]) != 1) {
        fprintf(stderr, "Error while reading color of node %d\n", i);
        exit(EXIT_FAILURE);
      }

    }
    printf("Finished reading list.\n"); 

    fclose(f);

    return 1;
  }

  return 0;
}

void process_prog_opt(char c, char *optarg) {
  if(c == 'e') {
    ERR = atoll(optarg);
  }
}

void output(CSRGraphTy &g, const char *output_file) {
  FILE *f;

  bool valid_coloring = true;

  for(int i = 0; i < g.nnodes; i++) {
    if(g.node_data[i] == 0) {
      valid_coloring = false;
      break;
    }
  }

  printf("Valid coloring : %s\n", valid_coloring ? "yes" : "no");	

  if(valid_coloring) 
    printf("Chromatic number : %d\n", CHROMATIC_NUMBER);
  if(!valid_coloring) 
    SKELAPP_RETVAL = 1;

  if(!output_file)
    return;

  if(strcmp(output_file, "-") == 0)
    f = stdout;
  else
    f = fopen(output_file, "w");

  // outputs conflicting nodes and the corresponding color
  // outputs first ERR conflicts

  if(!valid_coloring) {
    for(int node = 0; node < g.nnodes; node++) {
      for(int edge = g.row_start[node]; edge < g.row_start[node+1]; edge++) {
        int dst = g.edge_dst[edge];
        if(COLORS[node] == COLORS[dst] && node < dst) {
	  if(ERR != 0) {
            check_fprintf(f, "%d %d %d\n", node, dst, COLORS[node]);
	    if(ERR > 0) ERR--;
	  }
        }
      }
      if(ERR == 0) break;
    }
  }
}
