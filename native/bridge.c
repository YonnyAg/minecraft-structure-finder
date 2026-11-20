/* Small, versioned ABI: Python never depends on Cubiomes struct layouts. */
#include "finders.h"
#include <stdlib.h>

#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif

typedef struct { Generator generator; uint64_t seed; } Finder;

API int finder_abi(void) { return 1; }
API int finder_region_blocks(void) {
    StructureConfig config;
    return getStructureConfig(Swamp_Hut, MC_26_3, &config) ? config.regionSize * 16 : 0;
}
API void *finder_create(int64_t seed) {
    Finder *finder = malloc(sizeof(Finder));
    if (!finder) return NULL;
    finder->seed = (uint64_t)seed;
    setupGenerator(&finder->generator, MC_26_3, 0);
    applySeed(&finder->generator, DIM_OVERWORLD, finder->seed);
    return finder;
}
API void finder_free(void *context) { free(context); }
/* -1 = invalid context, 0 = no viable hut, 1 = biome-validated prediction. */
API int finder_hut(void *context, int rx, int rz, int *x, int *z) {
    Finder *finder = context;
    Pos pos;
    if (!finder || !x || !z) return -1;
    if (!getStructurePos(Swamp_Hut, MC_26_3, finder->seed, rx, rz, &pos)) return 0;
    if (!isViableStructurePos(Swamp_Hut, &finder->generator, pos.x, pos.z, 0)) return 0;
    *x = pos.x;
    *z = pos.z;
    return 1;
}
