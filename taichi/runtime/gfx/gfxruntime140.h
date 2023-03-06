// GfxRuntime140 convention data ser/de procedures. The structure of this file
// is in accordance with `python/taichi/aot/conventions/gfxruntime140/dr.py`.
#pragma once
#include "taichi/ir/type.h"
#include "taichi/common/serialization.h"

namespace taichi::lang {
namespace gfx {

enum PrimitiveTypeId {
  f16 = 0,
  f32 = 1,
  f64 = 2,
  i8 = 3,
  i16 = 4,
  i32 = 5,
  i64 = 6,
  u1 = 7,
  u8 = 8,
  u16 = 9,
  u32 = 10,
  u64 = 11,
  gen = 12,
  unknown = 13,
};

// This is merely a placeholder. GfxRuntime140 actually doesn't use this.
struct FieldAttributes {
  uint32_t dtype{0};
  std::string dtype_name;
  std::vector<int> element_shape;
  std::string field_name;
  bool is_scalar{false};
  size_t mem_offset_in_parent{0};
  std::vector<int> shape;
  TI_IO_DEF(dtype, dtype_name, element_shape, field_name, is_scalar, mem_offset_in_parent);
};

struct ArgumentAttributes {
    // For scalar arg, this is max(stride(dt), 4)
    // For array arg, this is #elements * max(stride(dt), 4)
    // Unit: byte
    size_t stride{0};
    // Offset in the context buffer
    size_t offset_in_mem{0};
    // Index of the input arg or the return value in the host `Context`
    int index{-1};
    PrimitiveTypeID dtype{PrimitiveTypeID::unknown};
    bool is_array{false};
    std::vector<int> element_shape;
    std::size_t field_dim{0};
    // Only used with textures. Sampled textures always have unknown format;
    // while RW textures always have a valid format.
    BufferFormat format{BufferFormat::unknown};
};

struct ContextAttributes {
  uint32_t 
};

struct KernelAttributes {
  // Taichi kernel name
  std::string name;
  // Is this kernel for evaluating the constant fold result?
  bool is_jit_evaluator{false};
  // Attributes of all the tasks produced from this single Taichi kernel.
  std::vector<TaskAttributes> tasks_attribs;

  KernelContextAttributes ctx_attribs;

  TI_IO_DEF(name, is_jit_evaluator, tasks_attribs, ctx_attribs);
};

struct Metadata {
  std::vector<KernelAttributes> kernels;
  std::vector<aot::CompiledFieldData> fields;
  std::map<std::string, uint32_t> required_caps;
  size_t root_buffer_size{0};
};

struct GfxRuntime140 {
  std::vector<> kernels;
  std::vector<std::string, uint32_t> required_caps;
};

} // namespace gfx
} // namespace taichi::lang
