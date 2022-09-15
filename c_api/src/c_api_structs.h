#pragma once
#include <taichi/taichi.h>

namespace detail {

template <typename T>
struct TiObjectTypeClassifier {
  static constexpr bool is(const void *obj) {
    return *(const TiObjectType *)obj == T::TY_;
  }
  static constexpr T *as(void *obj) {
    return *this;
  }
};

}  // namespace detail

struct TiObject {
  // Object type. Used to differentiate handle types from external calls.
  TiObjectType ty_;
  // Version of object. Used for compatibility if some object creation function
  // is superceeded by another newer version.
  uint32_t ver_;
};

enum TiObjectType {
  TI_OBJECT_TYPE_RUNTIME,
  TI_OBJECT_TYPE_AOT_MODULE,
  TI_OBJECT_TYPE_EVENT,
  TI_OBJECT_TYPE_MEMORY,
  TI_OBJECT_TYPE_IMAGE,
  TI_OBJECT_TYPE_SAMPLER,
  TI_OBJECT_TYPE_KERNEL,
  TI_OBJECT_TYPE_COMPUTE_GRAPH,
};

// Implementation types should derive from these.
namespace capi {
class Runtime;       // : TiRuntime_t {};
class AotModule;     // : TiAotModule_t {};
class Event;         // : TiEvent_t {};
class Memory;        // : TiMemory_t {};
class Image;         // : TiImage_t {};
class Sampler;       // : TiSampler_t {};
class Kernel;        // : TiKernel_t {};
class ComputeGraph;  // : TiComputeGraph_t {};
}  // namespace capi

struct TiRuntime_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_RUNTIME;
  TiObject obj_;
  void *dep;
};

struct TiAotModule_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_AOT_MODULE;
  TiObject obj_;
  capi::Runtime *dep;
};

struct TiEvent_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_EVENT;
  TiObject obj_;
  capi::Runtime *dep;
};

struct TiMemory_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_MEMORY;
  TiObject obj_;
  capi::Runtime *dep;
};

struct TiImage_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_IMAGE;
  TiObject obj_;
  capi::Runtime *dep;
};

struct TiSampler_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_SAMPLER;
  TiObject obj_;
  capi::Runtime *dep;
};

struct TiKernel_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_KERNEL;
  TiObject obj_;
  capi::AotModule *dep;
};

struct TiComputeGraph_t {
  static const TiObjectType TY_ = TI_OBJECT_TYPE_COMPUTE_GRAPH;
  TiObject obj_;
  capi::AotModule *dep;
};
