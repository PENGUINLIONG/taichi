import argparse
import json
import runpy
from pathlib import Path
from typing import List

from taichi._lib import core as _ti_core
from taichi._ti_module.cppgen import generate_header
from taichi.aot.conventions.gfxruntime140 import GfxRuntime140

import taichi as ti
from taichi.aot import _aot_kernels


def module_cppgen(parser: argparse.ArgumentParser):
    """Generate C++ headers for Taichi modules."""
    parser.add_argument("MODOLE", help="Path to the module directory.")
    parser.add_argument("-n",
                        "--namespace",
                        type=str,
                        help="C++ namespace if wanted.")
    parser.add_argument(
        "-m",
        "--module-name",
        type=str,
        help=
        "Module name to be a part of the module class. By default, it's the directory name.",
        default=None)
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        help="Output C++ header path.",
                        default="module.h")
    parser.set_defaults(func=module_cppgen_impl)


def module_cppgen_impl(a):
    module_path = a.MODOLE

    print(
        f"Generating C++ header for Taichi module: {Path(module_path).absolute()}"
    )

    if a.module_name:
        module_name = a.module_name
    else:
        module_name = Path(module_path).name
        if module_name.endswith(".tcm"):
            module_name = module_name[:-4]

    m = GfxRuntime140.from_module(module_path)

    out = generate_header(m, module_name, a.namespace)

    with open(a.output, "w") as f:
        f.write('\n'.join(out))

    print(f"Module header is saved to: {Path(a.output).absolute()}")


def module_build(parser: argparse.ArgumentParser):
    """Build Taichi modules from python scripts."""
    parser.add_argument(
        "SOURCE", help="Path to the Taichi program source (Python script).")
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        help="Output module path.",
                        default=None)
    parser.add_argument("-a",
                        "--arch",
                        type=str,
                        help="Target architecture.",
                        default="vulkan")
    parser.set_defaults(func=module_build_impl)


def module_build_impl(a):
    source_path = a.SOURCE
    module_path = a.output
    arch = _ti_core.arch_from_name(a.arch)

    source_path = Path(source_path)
    assert source_path.name.endswith(".py"), "Source must be a Python script."
    if module_path is None:
        module_path = f"{source_path.name[:-3]}.tcm"
    module_path = Path(module_path)

    print()
    print(f"Building Taichi module: {source_path}")

    d = runpy.run_path(str(source_path), run_name="__main__")

    required_caps = d["REQUIRED_CAPS"] if "REQUIRED_CAPS" in d else []
    assert isinstance(required_caps, list), "REQUIRED_CAPS must be a list."

    if required_caps:
        print("Module requires the following capabilities:")
        for cap in required_caps:
            print(f"  - {cap}")

    m = ti.aot.Module(caps=required_caps)
    for kernel in _aot_kernels:
        print("Added kernel:", kernel.__name__)
        m.add_kernel(kernel)

    if module_path.name.endswith(".tcm"):
        m.archive(str(module_path))
    else:
        m.save(str(module_path))

    print(f"Module is archive to: {module_path}")
    print()


def module(arguments: List[str]):
    """Taichi module tools."""
    parser = argparse.ArgumentParser(prog='ti module',
                                     description=module.__doc__)
    subparsers = parser.add_subparsers(title="Taichi module manager commands",
                                       required=True)

    cppgen_parser = subparsers.add_parser('cppgen', help=module_cppgen.__doc__)
    build_parser = subparsers.add_parser('build', help=module_build.__doc__)
    module_cppgen(cppgen_parser)
    module_build(build_parser)
    args = parser.parse_args(arguments)
    args.func(args)
