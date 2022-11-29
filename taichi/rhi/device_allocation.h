#pragma once
#include <cstdint>
#include "taichi/common/core.h"

namespace taichi::lang {

class Device;

struct DeviceAllocation;
struct DevicePtr;

// TODO: Figure out how to support images. Temporary solutions is to have all
// opque types such as images work as an allocation
using DeviceAllocationId = uint32_t;

struct TI_DLL_EXPORT DeviceAllocation {
  Device *device{nullptr};
  DeviceAllocationId alloc_id{0};
  // TODO: Shall we include size here?

  DevicePtr get_ptr(uint64_t offset = 0) const;

  bool operator==(const DeviceAllocation &other) const {
    return other.device == device && other.alloc_id == alloc_id;
  }

  bool operator!=(const DeviceAllocation &other) const {
    return !(*this == other);
  }
};

struct TI_DLL_EXPORT DeviceAllocationGuard : public DeviceAllocation {
  explicit DeviceAllocationGuard(DeviceAllocation alloc)
      : DeviceAllocation(alloc) {
  }
  DeviceAllocationGuard(const DeviceAllocationGuard &) = delete;
  ~DeviceAllocationGuard();
};

struct TI_DLL_EXPORT DevicePtr : public DeviceAllocation {
  uint64_t offset{0};

  bool operator==(const DevicePtr &other) const {
    return other.device == device && other.alloc_id == alloc_id &&
           other.offset == offset;
  }

  bool operator!=(const DevicePtr &other) const {
    return !(*this == other);
  }
};

constexpr DeviceAllocation kDeviceNullAllocation{};
constexpr DevicePtr kDeviceNullPtr{};

} // namespace taichi::lang