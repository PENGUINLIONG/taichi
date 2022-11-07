#include "asset_manager.h"

namespace taichi::lang {
namespace aot {

void AssetManager::load_module(ModuleData2& module) const {
  bool succ = false;

  std::string json;
  succ = load_text("metadata.json", json);
  TI_ERROR_UNLESS(succ, "cannot load metadata.json");
  liong::json::deserialize(liong::json::parse(json), module);

  for (size_t i = 0; i < module.artifacts.size(); ++i) {
    CompiledArtifact& artifact = module.artifacts.at(i);
    succ = load_bin(artifact.path, artifact.data);
    TI_ERROR_UNLESS(succ, "cannot load artifact {}", artifact.path);
  }
}
void AssetManager::save_module(const ModuleData2& module) const {
  bool succ = false;
  std::string json = liong::json::print(liong::json::serialize(module));
  succ = save_text("metadata.2.json", json);
  TI_ERROR_UNLESS(succ, "cannot save metadata.json");

  for (size_t i = 0; i < module.artifacts.size(); ++i) {
    const CompiledArtifact& artifact = module.artifacts.at(i);
    succ = save_bin(artifact.path, artifact.data);
    TI_ERROR_UNLESS(succ, "cannot save artifact {}", artifact.path);
  }
}

FilesystemAssetManager::FilesystemAssetManager(const std::string& output_dir) :
    output_dir(output_dir + "/") {
}

bool FilesystemAssetManager::load_text(const std::string& path, std::string& dst) const {
  std::fstream f(output_dir + path, std::ios::ate | std::ios::in);
  if (!f.is_open()) { return false; }

  dst.resize(f.tellg());
  f.seekg(std::ios::beg);
  f.read(dst.data(), dst.size());
  return true;
}
bool FilesystemAssetManager::load_bin(const std::string& path, std::vector<uint8_t>& dst) const {
  std::fstream f(output_dir + path, std::ios::ate | std::ios::in | std::ios::binary);
  if (!f.is_open()) { return false; }

  dst.resize(f.tellg());
  f.seekg(std::ios::beg);
  f.read((char*)dst.data(), dst.size());
  return true;
}

bool FilesystemAssetManager::save_text(const std::string& path, const std::string& src) const {
  std::fstream f(output_dir + path, std::ios::trunc | std::ios::out);
  if (!f.is_open()) { return false; }

  f << src;
  return true;
}
bool FilesystemAssetManager::save_bin(const std::string& path, const std::vector<uint8_t>& src) const {
  std::fstream f(output_dir + path, std::ios::trunc | std::ios::out | std::ios::binary);
  if (!f.is_open()) { return false; }

  f.write((const char*)src.data(), src.size());
  return true;
}

} // namespace aot
} // namespace taichi::lang
