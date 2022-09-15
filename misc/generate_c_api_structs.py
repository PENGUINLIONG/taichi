from taichi_json import (Name, EntryBase, Handle, Module)

# from os import system


def get_handle_object_type_name(x: EntryBase):
    return Name(str(x.name)).upper_camel_case


def get_handle_type_name(x: EntryBase):
    return x.name.upper_camel_case


def get_handle_struct_name(x: EntryBase):
    return x.name.upper_camel_case + "_t"


def get_handle_object_type_enum_case(x: EntryBase):
    return Name(str(x.name), prefix=["ti", "object", "type"]).screaming_snake_case


def print_handle_struct_header(module: Module, symbols):
    out = [
        "#pragma once",
        "#include <taichi/taichi.h>",
        "",
        "namespace detail {",
        "",
        "template<typename T>",
        "struct TiObjectTypeClassifier {",
        "  static constexpr bool is(const void* obj) {",
        "    return *(const TiObjectType*)obj == T::TY_;",
        "  }",
        "  static constexpr T* as(void* obj) {",
        "    return *this;",
        "  }",
        "};",
        "",
        "} // namespace detail",
        "",
        "struct TiObject {",
        "  // Object type. Used to differentiate handle types from external calls.",
        "  TiObjectType ty_;",
        "  // Version of object. Used for compatibility if some object creation function",
        "  // is superceeded by another newer version.",
        "  uint32_t ver_;",
        "};",
        "",
    ]

    # Generate handles' object types
    out += ["enum TiObjectType {"]
    for symbol in symbols:
        handle = module.declr_reg.resolve(symbol)
        out += [f"  {get_handle_object_type_enum_case(handle)},"]
    out += [
        "};",
        "",
    ]

    # Generate class definitions.
    out += [
        "// Implementation types should derive from these.",
        "namespace capi {",
    ]
    for symbol in symbols:
        handle = module.declr_reg.resolve(symbol)
        out += [f"class {get_handle_object_type_name(handle)}; // : {get_handle_struct_name(handle)}" + " {};"]
    out += [
        "} // namespace capi",
        "",
    ]

    # Generate class definitions.
    for symbol in symbols:
        handle = module.declr_reg.resolve(symbol)
        if handle.dependency is not None:
            dep_ty = f"capi::{get_handle_object_type_name(module.declr_reg.resolve(handle.dependency))}*"
        else:
            dep_ty = "void*"
        out += [
            f"struct {get_handle_struct_name(handle)} " + "{",
            f"  static const TiObjectType TY_ = {get_handle_object_type_enum_case(handle)};",
            "  TiObject obj_;",
            f"  {dep_ty} dep;",
            "};",
            "",
        ]

    path = f"c_api/src/c_api_structs.h"
    with open(path, "w") as f:
        f.write('\n'.join(out))

    # system(f"clang-format {path} -i")


if __name__ == "__main__":
    symbols = []
    for module in Module.load_all({}, True):
        for x in module.declr_reg:
            x2 = module.declr_reg.resolve(x)
            if type(x2) is Handle and x2.is_ptr is not True:
                symbols += [x]

    print_handle_struct_header(module, symbols)
