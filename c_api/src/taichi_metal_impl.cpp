#ifdef TI_WITH_METAL
#include "taichi_metal_impl.h"

// -----------------------------------------------------------------------------

TiRuntime ti_import_metal_runtime_ext(const TiMetalRuntimeInteropInfoExt *interop_info) {

  TiRuntime out = TI_NULL_HANDLE;

  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL_RV(interop_info);

  // In this case the 'metal' runtime (actually a MoltenVK Vulkan runtime) is
  // created on the systen default metal device.
  out = ti_create_runtime(TI_ARCH_METAL, 0);
  VulkanRuntime* vk_runtime = ((Runtime *)out)->as_vk();
  VkDevice vk_device = vk_runtime->get_vk().vk_device();

  VkExportMetalDeviceInfoEXT emdi{};
  emdi.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_DEVICE_INFO_EXT;

  VkExportMetalObjectsInfoEXT emoi{};
  emoi.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECTS_INFO_EXT;
  emoi.pNext = &emdi;

  auto vkExportMetalObjectsEXT_ = (PFN_vkExportMetalObjectsEXT)vkGetDeviceProcAddr(vk_device, "vkExportMetalObjectsEXT");
  vkExportMetalObjectsEXT_(vk_device, &emoi);

  // Simply check if the provided device is the system default device. We cannot
  // actually import a metal device to MoltenVK.
  if (emdi.mtlDevice != (MTLDevice_id)interop_info->device) {
    ti_set_last_error(
        TI_ERROR_INVALID_INTEROP,
        "imported metal device must be the system default device");
  }

  TI_CAPI_TRY_CATCH_END();
  return out;
}
TiMemory ti_import_metal_memory_ext(
    TiRuntime runtime,
    const TiMetalMemoryInteropInfoExt *interop_info) {
  TiMemory out = TI_NULL_HANDLE;
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL_RV(runtime);
  TI_CAPI_ARGUMENT_NULL_RV(interop_info);

  VulkanRuntime *runtime2 = ((Runtime *)runtime)->as_vk();
  VkDevice vk_device = runtime2->get_vk().vk_device();

  VkResult res = VK_SUCCESS;

  VkImportMetalBufferInfoEXT imbi{};
  imbi.sType = VK_STRUCTURE_TYPE_IMPORT_METAL_BUFFER_INFO_EXT;
  imbi.mtlBuffer = (MTLBuffer_id)interop_info->buffer;

  VkMemoryAllocateInfo mai{};
  mai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
  mai.pNext = &imbi;
  // FIXME: (penguinliong) Magic. I hope it works everywhere.
  mai.memoryTypeIndex = 0;
  mai.allocationSize = interop_info->size;

  VkDeviceMemory memory = VK_NULL_HANDLE; // FIXME: (penguinliong) Free this.
  res = vkAllocateMemory(vk_device, &mai, nullptr, &memory);
  TI_ERROR_IF(res != VK_SUCCESS, "ti_import_metal_memory_ext-vkAllocateMemory");

  VkBufferCreateInfo bci{};
  bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
  bci.size = interop_info->size;
  bci.usage =
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT |
    VK_BUFFER_USAGE_TRANSFER_DST_BIT |
    VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
  bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

  VkBuffer buffer = VK_NULL_HANDLE; // FIXME: (penguinliong) Destroy this.
  res = vkCreateBuffer(vk_device, &bci, nullptr, &buffer);
  TI_ERROR_IF(res != VK_SUCCESS, "ti_import_metal_memory_ext-vkCreateBuffer");

  res = vkBindBufferMemory(vk_device, buffer, memory, 0);
  TI_ERROR_IF(res != VK_SUCCESS, "ti_import_metal_memory_ext-vkBindBufferMemory");

  TiVulkanMemoryInteropInfo interop_info2{};
  interop_info2.buffer = buffer;
  interop_info2.size = interop_info->size;
  interop_info2.usage = 
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT |
    VK_BUFFER_USAGE_TRANSFER_DST_BIT |
    VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
  interop_info2.memory = memory;
  interop_info2.offset = 0;
  out = ti_import_vulkan_memory(runtime, &interop_info2);

  TI_CAPI_TRY_CATCH_END();
  return out;
}

#endif // TI_WITH_METAL
