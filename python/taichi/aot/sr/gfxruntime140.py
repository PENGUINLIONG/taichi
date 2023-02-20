"""
Structured representation of all JSON data structures following the
GfxRuntime140.
"""
from enum import Enum
from typing import Any, Optional
import taichi as ti
from abc import ABC
import taichi.aot.dr.gfxruntime140 as dr


class Argument(ABC):
    def __init__(self):
        pass


class ArgumentScalar(Argument):
    def __init__(self, index: int, dtype: int):
        self.index: int = index
        self.dtype: int = dtype


class NdArrayAccess(Enum):
    NoAccess = 0
    Read = 1
    Write = 2
    ReadWrite = 3


class ArgumentNdArray(Argument):
    def __init__(self, index: int, dtype: int, element_shape: list[int], ndim: int, access: NdArrayAccess):
        self.index: int = index
        self.dtype: int = dtype
        self.element_shape: list[int] = element_shape
        self.ndim: int = ndim
        self.access: NdArrayAccess = access


class ArgumentTexture(Argument):
    def __init__(self, index: int, ndim: int):
        self.index: int = index
        self.ndim: int = ndim


class ArgumentRwTexture(Argument):
    def __init__(self, index: int, fmt: ti.Format, ndim: int):
        self.index: int = index
        self.fmt: ti.Format = fmt
        self.ndim: int = ndim


class ReturnValue:
    def __init__(self, dtype: int):
        self.dtype: int = dtype


class Context:
    def __init__(self, args: list[Argument], ret: Optional[ReturnValue]):
        self.args: list[Argument] = args
        self.ret: Optional[ReturnValue] = ret


class BufferBindingType(Enum):
    Root = 0
    GlobalTmps = 1
    Args = 2
    Rets = 3
    ListGen = 4
    ExtArr = 5


class BufferBinding:
    def __init__(self, binding: int, iarg: int, buffer_bind_ty: BufferBindingType):
        self.binding: int = binding
        self.iarg: int = iarg
        self.buffer_bind_ty: BufferBindingType = buffer_bind_ty


class TextureBindingType(Enum):
    Texture = 0
    RwTexture = 1


class TextureBinding:
    def __init__(self, binding: int, iarg: int, texture_bind_ty: TextureBindingType):
        self.binding: int = binding
        self.iarg: int = iarg
        self.texture_bind_ty: TextureBindingType = texture_bind_ty


class TaskType(Enum):
    Serial = 0
    RangeFor = 1
    StructFor = 2
    MeshFor = 3
    ListGen = 4
    Gc = 5
    GcRc = 6


class LaunchGrid:
    def __init__(self, block_size: int, grid_size: int):
        self.block_size: int = block_size
        self.grid_size: int = grid_size


class Task:
    def __init__(self, name: str, task_ty: TaskType, buffer_binds: list[BufferBinding], texture_binds: list[TextureBinding], launch_grid: LaunchGrid):
        self.name: str = name
        self.task_ty: TaskType = task_ty
        self.buffer_binds: list[BufferBinding] = buffer_binds
        self.texture_binds: list[TextureBinding] = texture_binds
        self.launch_grid: LaunchGrid = launch_grid


class Field:
    def __init__(self, name: str, dtype: int, element_shape: list[int], shape: list[int], offset: int):
        self.name: str = name
        self.dtype: int = dtype
        self.element_shape: list[int] = element_shape
        self.shape: list[int] = shape
        self.offset: int = offset


class Kernel:
    def __init__(self, name: str, context: Context, tasks: list[Task]):
        self.name = name
        self.context: Context = context
        self.tasks: list[Task] = tasks


class Metadata:
    def __init__(self, fields: list[Field], kernels: list[Kernel], required_caps: list[ti.DeviceCapability], root_buffer_size: int):
        self.fields: dict[str, Field] = {x.name: x for x in fields}
        self.kernels: dict[str, Kernel] = {x.name: x for x in kernels}
        self.required_caps: list[ti.DeviceCapability] = required_caps
        self.root_buffer_size: int = root_buffer_size


def from_dr_field(d: dr.FieldAttributes) -> Field:
    return Field(d.field_name, d.dtype, d.element_shape, d.shape, d.mem_offset_in_parent)


def from_dr_kernel(d: dr.KernelAttributes) -> Kernel:
    assert d.is_jit_evaluator == False

    name = d.name

    class OpaqueArgumentType(Enum):
        NdArray = 0
        Texture = 1
        RwTexture = 2

    tasks = []
    iarg2arg_ty: dict[int, OpaqueArgumentType] = {}
    for task in d.tasks_attribs:
        # Collect buffer bindings.
        buffer_binds = []
        for buffer_bind in task.buffer_binds:
            binding = buffer_bind.binding
            iarg = buffer_bind.buffer.root_id
            buffer_ty = BufferBindingType(buffer_bind.buffer.type)
            buffer_binds += [BufferBinding(binding, iarg, buffer_ty)]
            if buffer_ty == BufferBindingType.ExtArr:
                iarg2arg_ty[buffer_bind.buffer.root_id] = OpaqueArgumentType.NdArray
            elif buffer_ty == BufferBindingType.Root:
                pass
            elif buffer_ty == BufferBindingType.Args:
                pass
            elif buffer_ty == BufferBindingType.ListGen:
                pass
            elif buffer_ty == BufferBindingType.Rets:
                pass
            elif buffer_ty == BufferBindingType.GlobalTmps:
                pass
            else:
                assert False

        # Collect texture bindings.
        texture_binds = []
        for texture_bind in task.texture_binds:
            binding = texture_bind.binding
            iarg = texture_bind.arg_id
            if texture_bind.is_storage:
                texture_binds += [TextureBinding(binding,
                                                 iarg, TextureBindingType.RwTexture)]
                iarg2arg_ty[iarg] = OpaqueArgumentType.RwTexture
            else:
                texture_binds += [TextureBinding(binding,
                                                 iarg, TextureBindingType.Texture)]
                iarg2arg_ty[iarg] = OpaqueArgumentType.Texture

        launch_grid = LaunchGrid(
            task.advisory_num_threads_per_group, task.advisory_total_num_threads)

        tasks += [Task(task.name, TaskType(task.task_type),
                       buffer_binds, texture_binds, launch_grid)]

    args = []
    for i, arg in enumerate(d.ctx_attribs.arg_attribs_vec_):
        assert i == arg.index
        if arg.is_array:
            # Opaque binding types.
            if iarg2arg_ty[arg.index]:
                binding_ty = iarg2arg_ty[arg.index]
                if binding_ty == OpaqueArgumentType.NdArray:
                    args += [ArgumentNdArray(arg.index, arg.dtype, arg.element_shape,
                                             arg.field_dim, NdArrayAccess(d.ctx_attribs.arr_access[i]))]
                elif binding_ty == OpaqueArgumentType.Texture:
                    args += [ArgumentTexture(arg.index, arg.field_dim)]
                elif binding_ty == OpaqueArgumentType.RwTexture:
                    args += [ArgumentRwTexture(arg.index,
                                               ti.Format(arg.format), arg.field_dim)]
                else:
                    assert False
        else:
            args += [ArgumentScalar(arg.index, arg.dtype)]

    assert len(d.ctx_attribs.ret_attribs_vec_) <= 1
    if len(d.ctx_attribs.ret_attribs_vec_) != 0:
        rv = ReturnValue(d.ctx_attribs.ret_attribs_vec_[0].dtype)
    else:
        rv = None

    context = Context(args, rv)

    return Kernel(name, context, tasks)


def from_dr_metadata(d: dr.Metadata) -> Metadata:
    fields = [from_dr_field(x) for x in d.fields]
    kernels = [from_dr_kernel(x) for x in d.kernels]
    required_caps = []
    for cap in d.required_caps:
        if cap.value == 1:
            required_caps += [cap.key]
        else:
            required_caps += [f"{cap.key}={cap.value}"]
    root_buffer_size = d.root_buffer_size

    return Metadata(fields, kernels, required_caps, root_buffer_size)


def to_dr_field(f: Field) -> dict[str, Any]:
    j = {
        "dtype": f.dtype,
        "dtype_name": ti._lib.core.data_type_name(ti._lib.core.get_primitive_data_type(f.dtype)),
        "element_shape": f.element_shape,
        "field_name": f.name,
        "is_scalar": len(f.element_shape) == 0,
        "mem_offset_in_parent": f.offset,
        "shape": f.shape,
    }
    return j


def to_dr_kernel(s: Kernel) -> dict[str, Any]:
    tasks = []
    for task in s.tasks:
        buffer_binds = []
        for buffer_bind in task.buffer_binds:
            j = {
                "binding": buffer_bind.binding,
                "buffer": {
                    "root_id": buffer_bind.iarg,
                    "type": buffer_bind.buffer_bind_ty.value,
                }
            }
            buffer_binds += [j]

        texture_binds = []
        for texture_bind in task.texture_binds:
            j = {
                "arg_id": texture_bind.iarg,
                "binding": texture_bind.binding,
                "is_storage": texture_bind.texture_bind_ty == TextureBindingType.RwTexture,
            }
            texture_binds += [j]

        if task.task_ty == TaskType.RangeFor:
            range_for_attribs = {
                "begin": 0,
                "const_begin": True,
                "const_end": True,
                "end": task.launch_grid.grid_size,
            }
        else:
            range_for_attribs = None

        j = {
            "advisory_num_threads_per_group": task.launch_grid.block_size,
            "advisory_total_num_threads": task.launch_grid.grid_size,
            "buffer_binds": buffer_binds,
            "name": task.name,
            "range_for_attribs": range_for_attribs,
            "task_type": task.task_ty.value,
            "texture_binds": texture_binds,
        }
        tasks += [j]

    args = []
    arg_bytes = 0
    arr_access = []
    arg_offset = 0
    for i, arg in enumerate(s.context.args):
        if isinstance(arg, ArgumentNdArray):
            j = {
                "dtype": arg.dtype,
                "element_shape": arg.element_shape,
                "field_dim": arg.ndim,
                "format": ti.Format.unknown,
                "index": arg.index,
                "is_array": True,
                "offset_in_mem": arg_offset,
                "stride": 4,
            }
            args += [j]
            arr_access += [arg.access.value]
        elif isinstance(arg, ArgumentTexture):
            j = {
                "dtype": 1,
                "element_shape": [],
                "field_dim": arg.ndim,
                "format": ti.Format.unknown,
                "index": arg.index,
                "is_array": True,
                "offset_in_mem": arg_offset,
                "stride": 4,
            }
            args += [j]
            arr_access += [0]
        elif isinstance(arg, ArgumentRwTexture):
            j = {
                "dtype": 1,
                "element_shape": [],
                "field_dim": arg.ndim,
                "format": arg.fmt,
                "index": arg.index,
                "is_array": True,
                "offset_in_mem": arg_offset,
                "stride": 4,
            }
            args += [j]
            arr_access += [0]
        elif isinstance(arg, ArgumentScalar):
            j = {
                "dtype": arg.dtype,
                "element_shape": [],
                "field_dim": 0,
                "format": ti.Format.unknown,
                "index": arg.index,
                "is_array": False,
                "offset_in_mem": arg_offset,
                "stride": ti._lib.core.data_type_size(ti._lib.core.get_primitive_data_type(arg.dtype)),
            }
            args += [j]
            arr_access += [0]
        else:
            assert False
        arg_offset += j["stride"]
        arg_bytes = max(arg_bytes, j["offset_in_mem"] + j["stride"])

    rets = []
    ret_bytes = 0
    if s.context.ret is not None:
        for i, ret in enumerate([s.context.ret]):
            j = {
                "dtype": ret.dtype,
                "element_shape": [],
                "field_dim": 0,
                "format": ti.Format.unknown,
                "index": i,
                "is_array": False,
                "offset_in_mem": 0,
                "stride": ti._lib.core.data_type_size(ti._lib.core.get_primitive_data_type(ret.dtype)),
            }
            rets += [j]
            ret_bytes = max(ret_bytes, j["offset_in_mem"] + j["stride"])

    ctx_attribs = {
        "arg_attribs_vec_": args,
        "args_bytes_": arg_bytes,
        "arr_access": arr_access,
        "extra_args_bytes_": 1536,
        "ret_attribs_vec_": rets,
        "rets_bytes_": ret_bytes,
    }

    j = {
        "is_jit_evaluator": False,
        "ctx_attribs": ctx_attribs,
        "name": s.name,
        "tasks_attribs": tasks,
    }
    return j


def to_dr_metadata(s: Metadata) -> dr.Metadata:
    fields = [to_dr_field(x) for x in s.fields.values()]
    kernels = [to_dr_kernel(x) for x in s.kernels.values()]
    required_caps = []
    for cap in s.required_caps:
        cap = str(cap)
        if "=" in cap:
            k, v = cap.split("=", maxsplit=1)
            j = {
                "key": k,
                "value": int(v),
            }
            required_caps += [j]
        else:
            j = {
                "key": cap,
                "value": 1,
            }
            required_caps += [j]
    root_buffer_size = s.root_buffer_size
    j = {
        "fields": fields,
        "kernels": kernels,
        "required_caps": required_caps,
        "root_buffer_size": root_buffer_size,
    }
    return dr.Metadata(j)


class NamedArgument:
    def __init__(self, name: str, arg: Argument):
        self.name = name
        self.arg = arg


class Dispatch:
    def __init__(self, kernel: Kernel, args: list[NamedArgument]):
        self.kernel = kernel
        self.args = args


class Graph:
    def __init__(self, name: str, dispatches: list[Dispatch]):
        self.name = name
        self.dispatches = dispatches


def from_dr_graph(meta: Metadata, j: dr.Graph) -> Graph:
    dispatches = []
    for dispatch in j.value.dispatches:
        kernel = meta.kernels[dispatch.kernel_name]
        args = []
        for i, symbolic_arg in enumerate(dispatch.symbolic_args):
            arg = kernel.context.args[i]
            args += [NamedArgument(symbolic_arg.name, arg)]
        dispatches += [Dispatch(kernel, args)]
    return Graph(j.key, dispatches)


def to_dr_graph(s: Graph) -> dr.Graph:
    dispatches = []
    for dispatch in s.dispatches:
        kernel = dispatch.kernel
        symbolic_args = []
        for arg in dispatch.args:
            if isinstance(arg.arg, ArgumentScalar):
                j = {
                    "dtype_id": arg.arg.dtype,
                    "element_shape": [],
                    "field_dim": 0,
                    "name": arg.name,
                    "num_channels": 0,
                    "tag": 0,
                }
                symbolic_args += [j]
            elif isinstance(arg.arg, ArgumentNdArray):
                j = {
                    "dtype_id": arg.arg.dtype,
                    "element_shape": arg.arg.element_shape,
                    "field_dim": arg.arg.ndim,
                    "name": arg.name,
                    "num_channels": 0,
                    "tag": 2,
                }
                symbolic_args += [j]
            elif isinstance(arg.arg, ArgumentTexture):
                j = {
                    "dtype_id": 1,
                    "element_shape": [],
                    "field_dim": 0,
                    "name": arg.name,
                    "num_channels": 0,
                    "tag": 3,
                }
                symbolic_args += [j]
            elif isinstance(arg.arg, ArgumentRwTexture):
                j = {
                    "dtype_id": 1,
                    "element_shape": [],
                    "field_dim": 0,
                    "name": arg.name,
                    "num_channels": 0,
                    "tag": 4,
                }
                symbolic_args += [j]
            else:
                assert False

        j = {
            "kernel_name": kernel.name,
            "symbolic_args": symbolic_args,
        }
        dispatches += [j]

    j = {
        "key": s.name,
        "value": {
            "dispatches": dispatches,
        },
    }
    return dr.Graph(j)
