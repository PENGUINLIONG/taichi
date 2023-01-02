#pragma once
#ifdef TI_WITH_METAL

#ifndef TI_WITH_VULKAN
static_assert(false, "Metal backend C-API must have Vulkan backend built");
#endif  // TI_WITH_VULKAN

#include "taichi_core_impl.h"
#include "taichi_vulkan_impl.h"

#endif // TI_WITH_METAL
