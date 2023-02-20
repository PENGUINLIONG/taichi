#include "taichi/aot/module_builder.h"
#include <fstream>
#include "taichi/common/json.h"
#include "taichi/common/json_serde.h"
#include "taichi/common/serialization.h"
#include "taichi/program/kernel.h"

namespace taichi::lang {

void AotModuleBuilder::add(const std::string &identifier, Kernel *kernel) {
  add_per_backend(identifier, kernel);
}

void AotModuleBuilder::add_field(const std::string &identifier,
                                 const SNode *rep_snode,
                                 bool is_scalar,
                                 DataType dt,
                                 std::vector<int> shape,
                                 int row_num,
                                 int column_num) {
  add_field_per_backend(identifier, rep_snode, is_scalar, dt, shape, row_num,
                        column_num);
}

void AotModuleBuilder::add_kernel_template(const std::string &identifier,
                                           const std::string &key,
                                           Kernel *kernel) {
  add_per_backend_tmpl(identifier, key, kernel);
}

bool AotModuleBuilder::all_fields_are_dense_in_container(
    const SNode *container) {
  for (const auto &ch : container->ch) {
    if (ch->type != SNodeType::place) {
      return false;
    }
  }
  const auto *parent = container->parent;
  if (!parent) {
    return false;
  }
  if (parent->type != SNodeType::root) {
    return false;
  }
  return true;
}

void AotModuleBuilder::load(const std::string &output_dir) {
  TI_ERROR("Aot loader not supported");
}

void AotModuleBuilder::dump_graph(std::string output_dir) const {
  std::string json_lit = liong::json::print(liong::json::serialize(graphs_));
  std::fstream f(output_dir + "/graphs.json", std::ios::out | std::ios::trunc);
  f.write((const char *)json_lit.data(), json_lit.size());
}

void AotModuleBuilder::add_graph(const std::string &name,
                                 const aot::CompiledGraph &graph) {
  if (graphs_.count(name) != 0) {
    TI_ERROR("Graph {} already exists", name);
  }
  // Handle adding kernels separately.
  std::unordered_map<std::string, lang::Kernel *> kernels;
  for (const auto &dispatch : graph.dispatches) {
    kernels[dispatch.kernel_name] = dispatch.ti_kernel;
  }
  for (auto &e : kernels) {
    add(e.first, e.second);
  }
  graphs_[name] = graph;
}
}  // namespace taichi::lang
