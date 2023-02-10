#pragma once

#include <taichi/taichi.h>

#ifdef __cplusplus
extern "C" {
#endif  // __cplusplus

// Handle `TiNsBundle`
typedef struct TiNsBundle_t *TiNsBundle;

// Handle `TiMtlDevice`
typedef struct TiMtlDevice_t *TiMtlDevice;

// Handle `TiMtlBuffer`
typedef struct TiMtlBuffer_t *TiMtlBuffer;

// Structure `TiMetalRuntimeInteropInfo`
typedef struct TiMetalRuntimeInteropInfo {
  TiNsBundle bundle;
  TiMtlDevice device;
} TiMetalRuntimeInteropInfo;

// Structure `TiMetalMemoryInteropInfo`
typedef struct TiMetalMemoryInteropInfo {
  TiMtlBuffer buffer;
  uint64_t size;
} TiMetalMemoryInteropInfo;

// Function `ti_import_metal_runtime`
TI_DLL_EXPORT TiRuntime TI_API_CALL
ti_import_metal_runtime(const TiMetalRuntimeInteropInfo *interop_info);

// Function `ti_export_metal_runtime`
TI_DLL_EXPORT void TI_API_CALL
ti_export_metal_runtime(TiRuntime runtime,
                        TiMetalRuntimeInteropInfo *interop_info);

// Function `ti_import_metal_memory`
TI_DLL_EXPORT TiMemory TI_API_CALL
ti_import_metal_memory(TiRuntime runtime,
                       const TiMetalMemoryInteropInfo *interop_info);

// Function `ti_export_metal_memory`
TI_DLL_EXPORT void TI_API_CALL
ti_export_metal_memory(TiRuntime runtime,
                       TiMemory memory,
                       TiMetalMemoryInteropInfo *interop_info);

#ifdef __cplusplus
}  // extern "C"
#endif  // __cplusplus
