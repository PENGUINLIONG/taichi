#include "taichi_ggui_impl.h"
#include "taichi/ui/backends/vulkan/window.h"
#include "taichi/program/compile_config.h"

TiWindowExt ti_create_window_ext(TiRuntime runtime, const TiWindowCreateInfoExt *create_info) {
    taichi::ui::AppConfig cfg {};
    cfg.name = create_info->title;
    cfg.width = create_info->width;
    cfg.height = create_info->height;
    cfg.vsync = create_info->vsync;
    cfg.show_window = taichi::lang::CompileConfig::default_compile_config.show;
    cfg.ti_arch = taichi::lang::CompileConfig::default_compile_config.arch;
    cfg.is_packed_mode = taichi::lang::CompileConfig::default_compile_config.packed;
    new taichi::ui::vulkan::Window()
}

void ti_destroy_window_ext(TiWindowExt window);

void ti_get_window_state_ext(TiWindowExt window, TiWindowStateExt *window_state);

TiCanvasExt ti_begin_frame_ext(TiWindowExt window);

TiCanvasExt ti_end_frame_ext();

void ti_draw_scene_ext(TiCanvasExt canvas,
                  TiMatrix4X4Ext camera_matrix,
                  uint32_t scene_light_count,
                  const TiSceneLightExt *scene_light,
                  uint32_t scene_object_count,
                  const TiSceneObjectExt *scene_objects);
