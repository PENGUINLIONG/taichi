option(USE_STDCPP "Use -stdlib=libc++" ON)
option(TI_WITH_LLVM "Build with LLVM backends" ON)
option(TI_WITH_METAL "Build with the Metal backend" ON)
option(TI_WITH_METAL2 "Build with the Metal backend" ON)
option(TI_WITH_CUDA "Build with the CUDA backend" ON)
option(TI_WITH_CUDA_TOOLKIT "Build with the CUDA toolkit" OFF)
option(TI_WITH_OPENGL "Build with the OpenGL backend" ON)
option(TI_WITH_CC "Build with the C backend" ON)
option(TI_WITH_VULKAN "Build with the Vulkan backend" OFF)
option(TI_WITH_DX11 "Build with the DX11 backend" OFF)
option(TI_WITH_DX12 "Build with the DX12 backend" OFF)
option(TI_WITH_GGUI "Build with GGUI" OFF)

# Force symbols to be 'hidden' by default so nothing is exported from the Taichi
# library including the third-party dependencies.
# As Taichi can be used by external projects, some of the internal dependencies
# such as Vulkan, ImGui, etc. could be in conflict with the dependencies of those
# projects.
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)
# Suppress warnings from submodules introduced by the above symbol visibility change
set(CMAKE_POLICY_DEFAULT_CMP0063 NEW)
set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)
set(INSTALL_LIB_DIR ${CMAKE_INSTALL_PREFIX}/python/taichi/_lib)

if(ANDROID)
    set(TI_WITH_VULKAN ON)
    set(TI_EXPORT_CORE ON)
    set(TI_WITH_LLVM OFF)
    set(TI_WITH_METAL OFF)
    set(TI_WITH_CUDA OFF)
    set(TI_WITH_OPENGL OFF)
    set(TI_WITH_CC OFF)
    set(TI_WITH_DX11 OFF)
    set(TI_WITH_DX12 OFF)
endif()

if(UNIX AND NOT APPLE)
    # Handy helper for Linux
    # https://stackoverflow.com/a/32259072/12003165
    set(LINUX TRUE)
endif()

if (APPLE)
    if (TI_WITH_CUDA)
        set(TI_WITH_CUDA OFF)
        message(WARNING "CUDA backend not supported on OS X. Setting TI_WITH_CUDA to OFF.")
    endif()
    if (TI_WITH_OPENGL)
        set(TI_WITH_OPENGL OFF)
        message(WARNING "OpenGL backend not supported on OS X. Setting TI_WITH_OPENGL to OFF.")
    endif()
    if (TI_WITH_CC)
        set(TI_WITH_CC OFF)
        message(WARNING "C backend not supported on OS X. Setting TI_WITH_CC to OFF.")
    endif()
endif()

if (WIN32)
    if (TI_WITH_CC)
        set(TI_WITH_CC OFF)
        message(WARNING "C backend not supported on Windows. Setting TI_WITH_CC to OFF.")
    endif()
endif()

if (NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/external/glad/src/gl.c")
    set(TI_WITH_OPENGL OFF)
    message(WARNING "external/glad submodule not detected. Settings TI_WITH_OPENGL to OFF.")
endif()

if(NOT TI_WITH_LLVM)
    set(TI_WITH_CUDA OFF)
    set(TI_WITH_CUDA_TOOLKIT OFF)
    set(TI_WITH_DX12 OFF)
endif()

file(GLOB TAICHI_CORE_SOURCE
    "taichi/analysis/*.cpp" "taichi/analysis/*.h"
    "taichi/ir/*"
    "taichi/jit/*"
    "taichi/math/*"
    "taichi/program/*"
    "taichi/struct/*"
    "taichi/system/*"
    "taichi/transforms/*"
    "taichi/aot/*.cpp" "taichi/aot/*.h"
    "taichi/platform/cuda/*" "taichi/platform/mac/*" "taichi/platform/windows/*"
    "taichi/codegen/*.cpp" "taichi/codegen/*.h"
    "taichi/runtime/*.h" "taichi/runtime/*.cpp"
    "taichi/rhi/*.h" "taichi/rhi/*.cpp"
)

if(TI_WITH_LLVM)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_LLVM")
endif()

## This version var is only used to locate slim_libdevice.10.bc
if(NOT CUDA_VERSION)
    set(CUDA_VERSION 10.0)
endif()

if (TI_WITH_CUDA)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_CUDA")
  file(GLOB TAICHI_CUDA_RUNTIME_SOURCE "taichi/runtime/cuda/runtime.cpp")
  list(APPEND TAICHI_CORE_SOURCE ${TAICHI_CUDA_RUNTIME_SOURCE})
endif()

if (TI_WITH_DX12)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_DX12")
endif()

## TODO: Remove CC backend
if (TI_WITH_CC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_CC")
  file(GLOB TAICHI_CC_SOURCE "taichi/codegen/cc/*.h" "taichi/codegen/cc/*.cpp")
  list(APPEND TAICHI_CORE_SOURCE ${TAICHI_CC_SOURCE})
endif()

set(CORE_LIBRARY_NAME taichi_core)
add_library(${CORE_LIBRARY_NAME} OBJECT ${TAICHI_CORE_SOURCE})

if (APPLE)
    # Ask OS X to minic Linux dynamic linking behavior
    set_target_properties(${CORE_LIBRARY_NAME}
      PROPERTIES INTERFACE_LINK_LIBRARIES "-undefined dynamic_lookup"
    )
endif()

target_include_directories(${CORE_LIBRARY_NAME} PRIVATE ${CMAKE_SOURCE_DIR})
target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/include)
target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/SPIRV-Tools/include)
target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/PicoSHA2)
target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/eigen)
target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/FP16/include)

if (TI_WITH_OPENGL OR TI_WITH_GGUI)
  set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
  set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
  set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)

  if (APPLE)
    set(GLFW_VULKAN_STATIC ON CACHE BOOL "" FORCE)
  endif()

  message("Building with GLFW")
  add_subdirectory(external/glfw)
  target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE glfw)
  target_include_directories(${CORE_LIBRARY_NAME} PUBLIC external/glfw/include)
endif()

if(TI_WITH_LLVM)
    if(DEFINED ENV{LLVM_DIR})
        set(LLVM_DIR $ENV{LLVM_DIR})
        message("Getting LLVM_DIR=${LLVM_DIR} from the environment variable")
    endif()

    # http://llvm.org/docs/CMake.html#embedding-llvm-in-your-project
    find_package(LLVM REQUIRED CONFIG)
    message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
    if(${LLVM_PACKAGE_VERSION} VERSION_LESS "10.0")
        message(FATAL_ERROR "LLVM version < 10 is not supported")
    endif()
    message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
    target_include_directories(${CORE_LIBRARY_NAME} PUBLIC ${LLVM_INCLUDE_DIRS})

    message("LLVM include dirs ${LLVM_INCLUDE_DIRS}")
    message("LLVM library dirs ${LLVM_LIBRARY_DIRS}")
    add_definitions(${LLVM_DEFINITIONS})

    llvm_map_components_to_libnames(llvm_libs
            Core
            ExecutionEngine
            InstCombine
            OrcJIT
            RuntimeDyld
            TransformUtils
            BitReader
            BitWriter
            Object
            ScalarOpts
            Support
            native
            Linker
            Target
            MC
            Passes
            ipo
            Analysis
            )

    if (APPLE AND "${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "arm64")
        llvm_map_components_to_libnames(llvm_aarch64_libs AArch64)
    endif()

    add_subdirectory(taichi/codegen/cpu)
    add_subdirectory(taichi/runtime/cpu)
    add_subdirectory(taichi/rhi/cpu)

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cpu_codegen)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cpu_runtime)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cpu_rhi)

    if (TI_WITH_CUDA)
        llvm_map_components_to_libnames(llvm_ptx_libs NVPTX)
        add_subdirectory(taichi/codegen/cuda)
        add_subdirectory(taichi/runtime/cuda)
        add_subdirectory(taichi/rhi/cuda)

        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cuda_codegen)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cuda_runtime)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE cuda_rhi)
    endif()

    if (TI_WITH_DX12)
        llvm_map_components_to_libnames(llvm_directx_libs DirectX)

        add_subdirectory(taichi/rhi/dx12)
        add_subdirectory(taichi/runtime/dx12)
        add_subdirectory(taichi/codegen/dx12)
        add_subdirectory(taichi/runtime/program_impls/dx12)

        target_include_directories(${CORE_LIBRARY_NAME} PRIVATE external/DirectX-Headers/include)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE dx12_codegen)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE dx12_runtime)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE dx12_program_impl)
    endif()

    add_subdirectory(taichi/rhi/llvm)
    add_subdirectory(taichi/codegen/llvm)
    add_subdirectory(taichi/runtime/llvm)
    add_subdirectory(taichi/runtime/program_impls/llvm)

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE llvm_program_impl)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE llvm_codegen)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE llvm_runtime)

    add_subdirectory(taichi/codegen/wasm)
    add_subdirectory(taichi/runtime/wasm)

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE wasm_codegen)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE wasm_runtime)

    if (LINUX)
        # Remove symbols from llvm static libs
        foreach(LETTER ${llvm_libs})
            target_link_options(${CORE_LIBRARY_NAME} PUBLIC -Wl,--exclude-libs=lib${LETTER}.a)
        endforeach()
    endif()
endif()

add_subdirectory(taichi/util)
add_subdirectory(taichi/common)
add_subdirectory(taichi/rhi/interop)

target_link_libraries(${CORE_LIBRARY_NAME} PUBLIC taichi_util)
target_link_libraries(${CORE_LIBRARY_NAME} PUBLIC taichi_common)
target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE interop_rhi)

if (TI_WITH_CUDA AND TI_WITH_CUDA_TOOLKIT)
    find_package(CUDAToolkit REQUIRED)
    message(STATUS "Found CUDAToolkit ${CUDAToolkit_VERSION}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_CUDA_TOOLKIT")
    target_include_directories(${CORE_LIBRARY_NAME} PUBLIC ${CUDAToolkit_INCLUDE_DIRS})
    target_link_libraries(${CORE_LIBRARY_NAME} PUBLIC CUDA::cupti)
endif()

if (TI_WITH_METAL)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_METAL")

    add_subdirectory(taichi/rhi/metal)
    add_subdirectory(taichi/runtime/metal)
    add_subdirectory(taichi/runtime/program_impls/metal)
    add_subdirectory(taichi/codegen/metal)
    add_subdirectory(taichi/cache/metal)

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE metal_codegen)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE metal_runtime)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE metal_program_impl)
endif()

if (TI_WITH_METAL2)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_METAL2")
endif()

if (TI_WITH_OPENGL)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_OPENGL")

    add_subdirectory(taichi/rhi/opengl)
    add_subdirectory(taichi/runtime/program_impls/opengl)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE opengl_program_impl)
endif()

if (TI_WITH_DX11)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_DX11")

    add_subdirectory(taichi/rhi/dx)
    add_subdirectory(taichi/runtime/program_impls/dx)
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE dx_program_impl)
endif()

# SPIR-V codegen is always there, regardless of Vulkan
set(SPIRV_SHARED_LIBRARIES OFF)
set(SPIRV_SKIP_EXECUTABLES ON)
set(SPIRV_SKIP_TESTS ON)
set(SKIP_SPIRV_TOOLS_INSTALL ON)
set(SPIRV_TOOLS_BUILD_STATIC ON)
set(SPIRV-Headers_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/external/SPIRV-Headers)

add_subdirectory(external/SPIRV-Tools)
add_subdirectory(taichi/codegen/spirv)
add_subdirectory(taichi/cache/gfx)
add_subdirectory(taichi/runtime/gfx)

if (TI_WITH_OPENGL OR TI_WITH_VULKAN OR TI_WITH_METAL2 OR TI_WITH_DX11)
  target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE spirv_codegen)
  target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE gfx_runtime)
endif()

if (TI_WITH_OPENGL OR TI_WITH_DX11)
  set(SPIRV_CROSS_CLI false)
  add_subdirectory(${PROJECT_SOURCE_DIR}/external/SPIRV-Cross ${PROJECT_BINARY_DIR}/external/SPIRV-Cross)
endif()

# Vulkan Device API
if (TI_WITH_VULKAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DTI_WITH_VULKAN")
    add_subdirectory(taichi/rhi/vulkan)
    if (APPLE)
        target_link_libraries(vulkan_rhi PUBLIC /Users/penguinliong/Library/Developer/Xcode/DerivedData/MoltenVK-gzvhtkjichuwfkckzndbkobvsjbr/Build/Products/Release/libMoltenVK.a)
        target_include_directories(vulkan_rhi PUBLIC /opt/homebrew/Cellar/molten-vk/1.2.1/include)
    endif()
    add_subdirectory(taichi/runtime/program_impls/vulkan)

    # TODO: this dependency is here because program.cpp includes vulkan_program.h
    # Should be removed
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE vulkan_rhi)

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE vulkan_program_impl)
endif ()


# Optional dependencies
if (APPLE)
    set(APPLE_FRAMEWORKS "")

    if (NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
        find_library(Cocoa NAMES Cocoa REQUIRED)
        list(APPEND APPLE_FRAMEWORKS ${Cocoa})
    endif()

    find_library(Metal NAMES Metal REQUIRED)
    list(APPEND APPLE_FRAMEWORKS ${Metal})

    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE ${APPLE_FRAMEWORKS})
endif ()

if (NOT WIN32)
    # Android has a custom toolchain so pthread is not available and should
    # link against other libraries as well for logcat and internal features.
    if (ANDROID)
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE android log)
    else()
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE pthread stdc++)
    endif()

    if (UNIX AND NOT ${CMAKE_SYSTEM_NAME} MATCHES "Linux")
	# OS X or BSD
    else()
        # Linux
        target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE stdc++fs X11)

        target_link_options(${CORE_LIBRARY_NAME} PRIVATE -static-libgcc -static-libstdc++)
        if (${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "x86_64")
            # Avoid glibc dependencies
            if (TI_WITH_VULKAN)
                target_link_options(${CORE_LIBRARY_NAME} PRIVATE -Wl,--wrap=log2f)
            else()
                # Enforce compatibility with manylinux2014
                target_link_options(${CORE_LIBRARY_NAME} PRIVATE -Wl,--wrap=log2f -Wl,--wrap=exp2 -Wl,--wrap=log2 -Wl,--wrap=logf -Wl,--wrap=powf -Wl,--wrap=exp -Wl,--wrap=log -Wl,--wrap=pow)
            endif()
        endif()
    endif()
else()
    # windows
    target_link_libraries(${CORE_LIBRARY_NAME} PRIVATE Winmm)
endif ()

foreach (source IN LISTS TAICHI_CORE_SOURCE)
    file(RELATIVE_PATH source_rel ${CMAKE_CURRENT_LIST_DIR} ${source})
    get_filename_component(source_path "${source_rel}" PATH)
    string(REPLACE "/" "\\" source_path_msvc "${source_path}")
    source_group("${source_path_msvc}" FILES "${source}")
endforeach ()

if(TI_WITH_PYTHON)
    # TODO Use TI_WITH_UI to guard the compilation of this target.
    # This requires refactoring on the python/export_*.cpp as well as better
    # error message on the Python side.
    add_subdirectory(taichi/ui)
    target_link_libraries(taichi_ui PUBLIC ${CORE_LIBRARY_NAME})

    message("PYTHON_LIBRARIES: " ${PYTHON_LIBRARIES})
    set(CORE_WITH_PYBIND_LIBRARY_NAME taichi_python)
    # Cannot compile Python source code with Android, but TI_EXPORT_CORE should be set and
    # Android should only use the isolated library ignoring those source code.
    if (NOT ANDROID)
        # NO_EXTRAS is required here to avoid llvm symbol error during build
        file(GLOB TAICHI_PYBIND_SOURCE
            "taichi/python/*.cpp"
            "taichi/python/*.h"
        )
        pybind11_add_module(${CORE_WITH_PYBIND_LIBRARY_NAME} NO_EXTRAS ${TAICHI_PYBIND_SOURCE})
    else()
        add_library(${CORE_WITH_PYBIND_LIBRARY_NAME} SHARED)
    endif ()

    # Remove symbols from static libs: https://stackoverflow.com/a/14863432/12003165
    if (LINUX)
        target_link_options(${CORE_WITH_PYBIND_LIBRARY_NAME} PUBLIC -Wl,--exclude-libs=ALL)
    endif()

    if (TI_WITH_BACKTRACE)
        # Defined by external/backward-cpp:
        # This will add libraries, definitions and include directories needed by backward
        # by setting each property on the target.
        target_link_libraries(${CORE_WITH_PYBIND_LIBRARY_NAME} PRIVATE ${BACKWARD_ENABLE})
    endif()

    if(TI_WITH_GGUI)
        target_compile_definitions(${CORE_WITH_PYBIND_LIBRARY_NAME} PRIVATE -DTI_WITH_GGUI)
        target_link_libraries(${CORE_WITH_PYBIND_LIBRARY_NAME} PRIVATE taichi_ui_vulkan)
    endif()

    target_link_libraries(${CORE_WITH_PYBIND_LIBRARY_NAME} PRIVATE taichi_ui)
    target_link_libraries(${CORE_WITH_PYBIND_LIBRARY_NAME} PRIVATE ${CORE_LIBRARY_NAME})

    target_include_directories(${CORE_WITH_PYBIND_LIBRARY_NAME}
      PRIVATE
        ${PROJECT_SOURCE_DIR}
        ${PROJECT_SOURCE_DIR}/external/spdlog/include
        ${PROJECT_SOURCE_DIR}/external/eigen
        ${PROJECT_SOURCE_DIR}/external/volk
        ${PROJECT_SOURCE_DIR}/external/SPIRV-Tools/include
        ${PROJECT_SOURCE_DIR}/external/Vulkan-Headers/include
        ${PROJECT_SOURCE_DIR}/external/imgui
        ${PROJECT_SOURCE_DIR}/external/imgui/backends
      )
    target_include_directories(${CORE_WITH_PYBIND_LIBRARY_NAME} SYSTEM
      PRIVATE
        ${PROJECT_SOURCE_DIR}/external/VulkanMemoryAllocator/include
      )

    if (TI_WITH_GGUI)
      target_include_directories(${CORE_WITH_PYBIND_LIBRARY_NAME}
        PRIVATE
          external/glfw/include
        )
    endif()

    # These commands should apply to the DLL that is loaded from python, not the OBJECT library.
    if (MSVC)
        set_property(TARGET ${CORE_WITH_PYBIND_LIBRARY_NAME} APPEND PROPERTY LINK_FLAGS /DEBUG)
    endif ()

    if (WIN32)
        set_target_properties(${CORE_WITH_PYBIND_LIBRARY_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY
                "${CMAKE_CURRENT_SOURCE_DIR}/runtimes")
    endif ()

    install(TARGETS ${CORE_WITH_PYBIND_LIBRARY_NAME}
            RUNTIME DESTINATION ${INSTALL_LIB_DIR}/core
            LIBRARY DESTINATION ${INSTALL_LIB_DIR}/core)
endif()

if (NOT APPLE)
    install(FILES ${CMAKE_SOURCE_DIR}/external/cuda_libdevice/slim_libdevice.10.bc
            DESTINATION ${INSTALL_LIB_DIR}/runtime)
endif()
