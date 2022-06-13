#pragma once
#include <taichi/taichi_platform.h>

// alias.bool
typedef uint32_t TiBool;

// definition.false
#define FALSE 0

// definition.true
#define TRUE 1

// alias.flags
typedef uint32_t TiFlags;

// definition.null_handle
#define NULL_HANDLE 0

// handle.runtime
typedef struct TiRuntime_t* TiRuntime;

// handle.aot_module
typedef struct TiAotModule_t* TiAotModule;

// handle.memory
typedef struct TiMemory_t* TiMemory;

// handle.kernel
typedef struct TiKernel_t* TiKernel;

// handle.compute_graph
typedef struct TiComputeGraph_t* TiComputeGraph;

// enumeration.arch
typedef enum TiArch {
  TI_ARCH_X64 = 0,
  TI_ARCH_ARM64 = 1,
  TI_ARCH_JS = 2,
  TI_ARCH_CC = 3,
  TI_ARCH_WASM = 4,
  TI_ARCH_CUDA = 5,
  TI_ARCH_METAL = 6,
  TI_ARCH_OPENGL = 7,
  TI_ARCH_DX11 = 8,
  TI_ARCH_OPENCL = 9,
  TI_ARCH_AMDGPU = 10,
  TI_ARCH_VULKAN = 11,
  TI_ARCH_MAX_ENUM = 0xffffffff,
};

// enumeration.argument_type
typedef enum TiArgumentType {
  TI_ARGUMENT_TYPE_I32 = 0,
  TI_ARGUMENT_TYPE_F32 = 1,
  TI_ARGUMENT_TYPE_NDARRAY = 2,
  TI_ARGUMENT_TYPE_MAX_ENUM = 0xffffffff,
};

// bit_field.memory_usage
enum TiMemoryUsageFlagBits {
  TI_MEMORY_USAGE_STORAGE_BIT = 0,
  TI_MEMORY_USAGE_UNIFORM_BIT = 1,
  TI_MEMORY_USAGE_VERTEX_BIT = 2,
  TI_MEMORY_USAGE_INDEX_BIT = 3,
};
typedef TiFlags TiMemoryUsageFlags;

// structure.memory_allocation_info
struct TiMemoryAllocationInfo {
  uint64_t size;
  bool host_write;
  bool host_read;
  bool export_sharing;
  TiMemoryUsageFlagBits usage;
};

// structure.nd_shape
struct TiNdShape {
  uint32_t dim_count;
  uint32_t dims;
};

// structure.nd_array
struct TiNdArray {
  TiMemory memory;
  TiNdShape shape;
  TiNdShape elem_shape;
};

// union.argument_value
union TiArgumentValue {
};

// structure.argument
struct TiArgument {
  TiArgumentType type;
  TiArgumentValue value;
};

// structure.named_argument
struct TiNamedArgument {
  const char* name;
  TiArgument argument;
};
