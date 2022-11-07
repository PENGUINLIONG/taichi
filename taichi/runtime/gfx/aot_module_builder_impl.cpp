#include "taichi/runtime/gfx/aot_module_builder_impl.h"

#include <fstream>
#include <type_traits>

#include "taichi/aot/module_data.h"
#include "taichi/codegen/spirv/spirv_codegen.h"
#include "taichi/runtime/gfx/aot_graph_data.h"

namespace taichi::lang {
namespace gfx {

AotModuleBuilderImpl::AotModuleBuilderImpl(
    const std::vector<CompiledSNodeStructs> &compiled_structs,
    Arch device_api_backend,
    const DeviceCapabilityConfig &caps)
    : compiled_structs_(compiled_structs),
      device_api_backend_(device_api_backend),
      caps_(caps) {
  for (const auto &pair : caps.to_inner()) {
    ti_aot_data_.required_caps[to_string(pair.first)] = pair.second;
  }
  if (!compiled_structs.empty()) {
    ti_aot_data_.root_buffer_size = compiled_structs[0].root_size;
  }
}

std::string AotModuleBuilderImpl::write_spv_file(
    const std::string &output_dir,
    const TaskAttributes &k,
    const std::vector<uint32_t> &source_code) const {
  const std::string spv_path = fmt::format("{}/{}.spv", output_dir, k.name);
  std::ofstream fs(spv_path, std::ios_base::binary | std::ios::trunc);
  fs.write((char *)source_code.data(), source_code.size() * sizeof(uint32_t));
  fs.close();
  return spv_path;
}

void AotModuleBuilderImpl::dump_kernels(const std::string &output_dir) const {
  const std::string bin_path = fmt::format("{}/metadata.tcb", output_dir);
  write_to_binary_file(ti_aot_data_, bin_path);

  std::string json = liong::json::print(liong::json::serialize(ti_aot_data_));
  std::fstream f(output_dir + "/metadata.json", std::ios::trunc | std::ios::out);
  f.write(json.data(), json.size());





  std::vector<aot::CompiledArtifact> artifacts {};
  for (size_t i = 0; i < ti_aot_data_.kernels; ++i) {
    const spirv::TaichiKernelAttributes& kernel_attr = ti_aot_data_.kernels.at(i);
    const std::vector<std::vector<uint32_t>> spirv_codes = ti_aot_data_.spirv_codes.at(i);

    for (size_t j = 0; j < kernel_attr.tasks_attribs; ++j) {
      const spirv::TaskAttributes& task_attr = kernel_attr.tasks_attribs.at(j);
      const std::vector<uint32_t>& spirv_code = spirv_codes.at(j);

      aot::CompiledArtifact artifact {};
      artifact.name = kernel_attr.name;
      artifact.path = kernel_attr.name + ".spv";
      artifact.data = std::vector<uint8_t>(
          (const uint8_t*)spirv_code.data(),
          (const uint8_t*)(spirv_code.data() + spirv_code.size()));
      artifacts.emplace_back(artifacts);
    }
  }

  struct GfxModuleExtra {
    uint root_buffer_size;
  } extra;
  extra.root_buffer_size = ti_aot_data_.root_buffer_size;


  aot::ModuleData2 mod {};
  mod.required_caps = caps_;
  mod.extra = liong::json::serialize(extra);
  mod.artifacts = std::move(artifacts);

  aot::FilesystemAssetManager asset_mgr(output_dir);
  asset_mgr.save_module(mod);
}

void AotModuleBuilderImpl::mangle_aot_data() {
  // Only for offline cache
  for (auto &kernel : ti_aot_data_.kernels) {
    const auto &prefix = kernel.name;
    for (std::size_t i = 0; i < kernel.tasks_attribs.size(); ++i) {
      kernel.tasks_attribs[i].name = prefix + std::to_string(i);
    }
  }
}

void AotModuleBuilderImpl::merge_with_old_meta_data(const std::string &path) {
  // Only for offline cache
  auto filename = taichi::join_path(path, "metadata.tcb");
  if (taichi::path_exists(filename)) {
    TaichiAotData old_data;
    read_from_binary_file(old_data, filename);
    // Ignore root_buffer_size and fields which aren't needed for offline cache
    ti_aot_data_.kernels.insert(ti_aot_data_.kernels.end(),
                                old_data.kernels.begin(),
                                old_data.kernels.end());
  }
}

std::optional<GfxRuntime::RegisterParams>
AotModuleBuilderImpl::try_get_kernel_register_params(
    const std::string &kernel_name) const {
  const auto &kernels = ti_aot_data_.kernels;
  for (std::size_t i = 0; i < kernels.size(); ++i) {
    if (kernels[i].name == kernel_name) {
      GfxRuntime::RegisterParams result;
      result.kernel_attribs = kernels[i];
      result.task_spirv_source_codes = ti_aot_data_.spirv_codes[i];
      // We only support a single SNodeTree during AOT.
      result.num_snode_trees = 1;
      return result;
    }
  }
  return std::nullopt;
}

void AotModuleBuilderImpl::add_per_backend(const std::string &identifier,
                                           Kernel *kernel) {
  spirv::lower(kernel);
  auto compiled =
      run_codegen(kernel, this->device_api_backend_, caps_, compiled_structs_);
  compiled.kernel_attribs.name = identifier;
  ti_aot_data_.kernels.push_back(compiled.kernel_attribs);
  ti_aot_data_.spirv_codes.push_back(compiled.task_spirv_source_codes);
}

void AotModuleBuilderImpl::add_field_per_backend(const std::string &identifier,
                                                 const SNode *rep_snode,
                                                 bool is_scalar,
                                                 DataType dt,
                                                 std::vector<int> shape,
                                                 int row_num,
                                                 int column_num) {
  // Note that currently we only support adding dense fields in AOT for all
  // backends. In opengl backend we only error out when a non dense field is
  // added to the aot module, but in metal backend we error out earlier when
  // constructing aot module. Ideally we will unify this behavior but it doesn't
  // matter too much for now.
  TI_ERROR_IF(!all_fields_are_dense_in_container(rep_snode->parent),
              "AOT: only supports dense field");

  const auto &dense_desc =
      compiled_structs_[0].snode_descriptors.at(rep_snode->parent->id);

  aot::CompiledFieldData field_data;
  field_data.field_name = identifier;
  field_data.is_scalar = is_scalar;
  field_data.dtype = static_cast<int>(dt->cast<PrimitiveType>()->type);
  field_data.dtype_name = dt.to_string();
  field_data.shape = shape;
  field_data.mem_offset_in_parent = dense_desc.mem_offset_in_parent_cell;
  if (!is_scalar) {
    field_data.element_shape = {row_num, column_num};
  }
  ti_aot_data_.fields.push_back(field_data);
}

void AotModuleBuilderImpl::add_per_backend_tmpl(const std::string &identifier,
                                                const std::string &key,
                                                Kernel *kernel) {
  spirv::lower(kernel);
  auto compiled =
      run_codegen(kernel, device_api_backend_, caps_, compiled_structs_);

  compiled.kernel_attribs.name = identifier + "|" + key;
  ti_aot_data_.kernels.push_back(compiled.kernel_attribs);
  ti_aot_data_.spirv_codes.push_back(compiled.task_spirv_source_codes);
}

}  // namespace gfx
}  // namespace taichi::lang
