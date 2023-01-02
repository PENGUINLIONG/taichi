#pragma once

#include <taichi/taichi.h>

#ifdef __cplusplus
extern "C" {
#endif  // __cplusplus

// Handle `TiNsBundleExt`
typedef struct TiNsBundleExt_t *TiNsBundleExt;

// Handle `TiMtlDeviceExt`
typedef struct TiMtlDeviceExt_t *TiMtlDeviceExt;

// Handle `TiMtlBufferExt`
typedef struct TiMtlBufferExt_t *TiMtlBufferExt;

// Structure `TiMetalRuntimeInteropInfoExt`
typedef struct TiMetalRuntimeInteropInfoExt {
  TiNsBundleExt bundle;
  TiMtlDeviceExt device;
} TiMetalRuntimeInteropInfoExt;

// Structure `TiMetalMemoryInteropInfoExt`
typedef struct TiMetalMemoryInteropInfoExt {
  TiMtlBufferExt buffer;
  uint64_t size;
} TiMetalMemoryInteropInfoExt;

// Function `ti_import_metal_runtime_ext`
TI_DLL_EXPORT TiRuntime TI_API_CALL
ti_import_metal_runtime_ext(const TiMetalRuntimeInteropInfoExt *interop_info);

// Function `ti_export_metal_runtime_ext`
TI_DLL_EXPORT void TI_API_CALL
ti_export_metal_runtime_ext(TiRuntime runtime,
                            TiMetalRuntimeInteropInfoExt *interop_info);

// Function `ti_import_metal_memory_ext`
TI_DLL_EXPORT TiMemory TI_API_CALL
ti_import_metal_memory_ext(TiRuntime runtime,
                           const TiMetalMemoryInteropInfoExt *interop_info);

// Function `ti_export_metal_memory_ext`
TI_DLL_EXPORT void TI_API_CALL
ti_export_metal_memory_ext(TiRuntime runtime,
                           TiMemory memory,
                           TiMetalMemoryInteropInfoExt *interop_info);

#ifdef __cplusplus
}  // extern "C"
#endif  // __cplusplus
