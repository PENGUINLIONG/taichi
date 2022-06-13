#pragma once
#include <taichi/taichi_core.h>
#include <vulkan/vulkan.h>

// structure.vulkan_runtime_interop_info
struct TiVulkanRuntimeInteropInfo {
  uint32_t api_version;
  VkInstance instance;
  VkPhysicalDevice physical_device;
  VkDevice device;
  VkQueue compute_queue;
  uint32_t compute_queue_family_index;
  VkQueue graphics_queue;
  uint32_t graphics_queue_family_index;
};

// structure.vulkan_memory_interop_info
struct TiVulkanMemoryInteropInfo {
  VkBuffer buffer;
  size_t size;
  VkBufferUsageFlags usage;
};

// function.create_vulkan_runtime
TI_DLL_EXPORT TiRuntime TI_API_CALL ti_create_vulkan_runtime_ext(
  uint32_t api_version,
  uint32_t instance_extension_count,
  const char** instance_extensions,
  uint32_t device_extension_count,
  const char** device_extensions
);

// function.import_vulkan_runtime
TI_DLL_EXPORT TiRuntime TI_API_CALL ti_import_vulkan_runtime(
  TiVulkanRuntimeInteropInfo interop_info
);

// function.export_vulkan_runtime
TI_DLL_EXPORT void TI_API_CALL ti_export_vulkan_runtime(
  TiRuntime runtime,
  TiVulkanRuntimeInteropInfo interop_info
);

// function.import_vulkan_memory
TI_DLL_EXPORT TiMemory TI_API_CALL ti_import_vulkan_memory(
  TiVulkanMemoryInteropInfo interop_info
);

// function.export_vulkan_memory
TI_DLL_EXPORT void TI_API_CALL ti_export_vulkan_memory(
  TiMemory memory,
  TiVulkanMemoryInteropInfo interop_info
);
