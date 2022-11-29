#pragma once
#include <cstring>
#include <vector>
#include "taichi/rhi/device_allocation.h"

namespace taichi::lang {

enum class ResourceType : uint32_t {
  uniform_buffer,
  storage_buffer,
  vertex_buffer,
  index_buffer,
  sampled_image,
  storage_image,
};

enum class IndexType : uint32_t {
  u16,
  u32,
};

struct ResourceBinding {
  ResourceType type;
  union {
    struct {
      uint32_t set;
      uint32_t binding;
      DeviceAllocation buffer;
    } uniform_buffer;
    struct {
      uint32_t set;
      uint32_t binding;
      DeviceAllocation buffer;
    } storage_buffer;
    struct {
      uint32_t binding;
      DeviceAllocation buffer;
    } vertex_buffer;
    struct {
      IndexType index_type;
      DeviceAllocation buffer;
    } index_buffer;
    struct {
      uint32_t set;
      uint32_t binding;
      // TODO: (penguinliong) Support samplers here.
      DeviceAllocation image;
    } sampled_image;
    struct {
      uint32_t set;
      uint32_t binding;
      uint32_t lod;
      DeviceAllocation image;
    } storage_image;
  };
};

class ResourceBinder {
 public:
  std::vector<ResourceBinding> bindings;

  // In Vulkan this is called Storage Buffer (shader can store)
  void rw_buffer(uint32_t set,
                 uint32_t binding,
                 DeviceAllocation alloc);

  // In Vulkan this is called Uniform Buffer (shader can only load)
  void buffer(uint32_t set,
              uint32_t binding,
              DeviceAllocation alloc);

  // TODO: (penguinliong) Support samplers here.
  void image(uint32_t set,
             uint32_t binding,
             DeviceAllocation alloc);

  void rw_image(uint32_t set,
                uint32_t binding,
                DeviceAllocation alloc,
                uint32_t lod);

  // Set vertex buffer (not implemented in compute only device)
  void vertex_buffer(DeviceAllocation alloc, uint32_t binding);

  // Set index buffer (not implemented in compute only device)
  // index_width = 4 -> uint32 index
  // index_width = 2 -> uint16 index
  void index_buffer(DeviceAllocation alloc, IndexType index_type);
};

struct ResourceBindingPoint {
  ResourceType type;
  uint32_t binding;
};
struct ResourceLayout {
  std::vector<ResourceBindingPoint> binding_points;

  friend bool operator<(const ResourceLayout& a, const ResourceLayout& b) {
    if (a.binding_points.size() >= b.binding_points.size()) {
      return false;
    }
    return std::memcmp(a.binding_points.data(), b.binding_points.data(),
        a.binding_points.size() * sizeof(ResourceBindingPoint)) < 0;
  }
};

} // namespace taichi::lang
