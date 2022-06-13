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
