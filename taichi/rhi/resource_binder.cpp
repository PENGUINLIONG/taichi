#pragma once
#include "taichi/rhi/resource_binder.h"

namespace taichi::lang {

// In Vulkan this is called Storage Buffer (shader can store)
void ResourceBinder::rw_buffer(uint32_t set,
                uint32_t binding,
                DeviceAllocation alloc) {
  ResourceBinding& b = bindings.emplace_back();
  b.type = ResourceType::storage_buffer;
  b.storage_buffer.set = set;
  b.storage_buffer.binding = binding;
  b.storage_buffer.buffer = alloc;
}

// In Vulkan this is called Uniform Buffer (shader can only load)
void ResourceBinder::buffer(uint32_t set,
            uint32_t binding,
            DeviceAllocation alloc) {
  ResourceBinding &b = bindings.emplace_back();
  b.type = ResourceType::uniform_buffer;
  b.uniform_buffer.set = set;
  b.uniform_buffer.binding = binding;
  b.uniform_buffer.buffer = alloc;
}

// TODO: (penguinliong) Support samplers here.
void ResourceBinder::image(uint32_t set,
            uint32_t binding,
            DeviceAllocation alloc) {
ResourceBinding &b = bindings.emplace_back();
b.type = ResourceType::sampled_image;
b.storage_image.image = alloc;
}

void ResourceBinder::rw_image(uint32_t set,
            uint32_t binding,
            DeviceAllocation alloc,
            uint32_t lod) {
ResourceBinding& b = bindings.emplace_back();
b.type = ResourceType::storage_image;
b.storage_image.lod = lod;
b.storage_image.image = alloc;
}

// Set vertex buffer (not implemented in compute only device)
void ResourceBinder::vertex_buffer(DeviceAllocation alloc, uint32_t binding) {
ResourceBinding& b = bindings.emplace_back();
b.type = ResourceType::vertex_buffer;
b.vertex_buffer.binding = binding;
b.vertex_buffer.buffer = alloc;
}

// Set index buffer (not implemented in compute only device)
// index_width = 4 -> uint32 index
// index_width = 2 -> uint16 index
void ResourceBinder::index_buffer(DeviceAllocation alloc, IndexType index_type) {
ResourceBinding& b = bindings.emplace_back();
b.type = ResourceType::index_buffer;
b.index_buffer.index_type = index_type;
b.index_buffer.buffer = alloc;
}

} // namespace taichi::lang
