#pragma once
#include "taichi/common/core.h"
#include "taichi/common/serialization.h"
#include "taichi/aot/module_data.h"

namespace taichi::lang {
namespace aot {

struct AssetManager {
  virtual bool load_text(const std::string& path, std::string& dst) const = 0;
  virtual bool load_bin(const std::string& path, std::vector<uint8_t>& dst) const = 0;

  virtual bool save_text(const std::string& path, const std::string& src) const = 0;
  virtual bool save_bin(const std::string& path, const std::vector<uint8_t>& src) const = 0;

  void load_module(ModuleData2& module) const;
  void save_module(const ModuleData2& module) const;
};

// Direct access to filesystem files.
struct FilesystemAssetManager : public AssetManager {
  const std::string output_dir;

  FilesystemAssetManager(const std::string& output_dir);

  virtual bool load_text(const std::string& path, std::string& dst) const override;
  virtual bool load_bin(const std::string& path, std::vector<uint8_t>& dst) const override;

  virtual bool save_text(const std::string& path, const std::string& src) const override;
  virtual bool save_bin(const std::string& path, const std::vector<uint8_t>& src) const override;
};

} // namespace aot
} // namespace taichi::lang