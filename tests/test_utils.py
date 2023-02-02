import copy
import functools
import itertools
import json
import os
import pathlib
import platform
import re
from errno import EEXIST
from tempfile import NamedTemporaryFile, mkstemp

import numpy as np
import pytest
from taichi._lib import core as _ti_core
from taichi.lang import cc, cpu, cuda, dx11, gles, gpu, metal, opengl, vulkan
from taichi.lang.misc import is_arch_supported

import taichi as ti


def expected_archs():
    """
    Reads the environment variable `TI_WANTED_ARCHS` (usually set by option `-a` in `python tests/run_tests.py`)
    and gets all expected archs on the machine.
    If `TI_WANTED_ARCHS` is set and does not start with `^`, archs specified in it will be returned.
    If `TI_WANTED_ARCHS` starts with `^` (usually when option `-n` is specified in `python tests/run_tests.py`),
    all supported archs except archs specified in it will be returned.
    If `TI_WANTED_ARCHS` is not set, all supported archs will be returned.
    Returns:
        List[taichi_python.Arch]: All expected archs on the machine.
    """
    archs = set([cpu, cuda, metal, vulkan, opengl, cc, gles])
    # TODO: now expected_archs is not called per test so we cannot test it
    archs = set(filter(is_arch_supported, archs))

    wanted_archs = os.environ.get('TI_WANTED_ARCHS', '')
    want_exclude = wanted_archs.startswith('^')
    if want_exclude:
        wanted_archs = wanted_archs[1:]
    wanted_archs = wanted_archs.split(',')
    # Note, ''.split(',') gives you [''], which is not an empty array.
    expanded_wanted_archs = set([])
    for arch in wanted_archs:
        if arch == '':
            continue
        if arch == 'cpu':
            expanded_wanted_archs.add(cpu)
        elif arch == 'gpu':
            expanded_wanted_archs.update(gpu)
        else:
            expanded_wanted_archs.add(_ti_core.arch_from_name(arch))
    if len(expanded_wanted_archs) == 0:
        return list(archs)
    if want_exclude:
        expected = archs - expanded_wanted_archs
    else:
        expected = expanded_wanted_archs
    return list(expected)


def print_section(message, symbol="-"):
    length = len(message)
    vert_border_length = 4

    section_horiz_border = symbol * (length + 2 + vert_border_length * 2)
    vert_border = symbol * vert_border_length
    message = f"{vert_border} {message} {vert_border}"

    print(section_horiz_border)
    print(message)
    print(section_horiz_border)


def parse_test_configs():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    test_config_path = os.path.join(curr_dir, "test_config.json")
    with open(test_config_path, "r") as f:
        test_config = json.loads(f.read())

    assert ("aot_test_cases" in test_config.keys())
    assert ("capi_aot_test_cases" in test_config.keys())

    for cpp_test_name, value in test_config["aot_test_cases"].items():
        test_paths = value[0]
        test_args = value[1]
        test_config["aot_test_cases"][cpp_test_name] = [
            os.path.join(*test_paths), test_args
        ]

    for cpp_test_name, value in test_config["capi_aot_test_cases"].items():
        test_paths = value[0]
        test_args = value[1]
        test_config["capi_aot_test_cases"][cpp_test_name] = [
            os.path.join(*test_paths), test_args
        ]

    return test_config["aot_test_cases"], test_config["capi_aot_test_cases"]


__aot_test_cases, __capi_aot_test_cases = parse_test_configs()


# FIXME: (penguinliong) The test extraction discovery is kind of a mess.
def parse_test_configs2():
    archs = expected_archs()
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    test_config_path = os.path.join(curr_dir, "test_config.json")
    with open(test_config_path, "r") as f:
        test_config = json.loads(f.read())

    assert ("capi_aot_test_cases" in test_config.keys())
    capi_aot_test_cases = {}
    for cpp_test_name, value in test_config["capi_aot_test_cases"].items():
        test_paths = value[0]
        test_args = value[1]
        skip_this = False
        for test_arg in test_args.split(' '):
            m = re.match(r'--arch=(\w+)', test_arg)
            arch = m and _ti_core.arch_from_name(m[1])
            if m and arch not in archs:
                print(
                    f"WARNING: ignored cpp test '{cpp_test_name}' because '{arch}' is not supported"
                )
                skip_this = True
                break
        if skip_this:
            continue
        capi_aot_test_cases[cpp_test_name] = [
            os.path.join(*test_paths), test_args
        ]

    return capi_aot_test_cases


def print_aot_test_guide():
    message = f"""
[ AOT Unit Tests Programming Guide ]

An AOT test is usually composed of:
1. A python script that compiles the Kernels and serialize into file.
2. A C++ test that loads the file then perform execution.

AOT test writer will have to configure your test case for "__aot_test_cases" in "test_config.json",
the format of which follows:

        "cpp_test_name" : [["python_program_path"], "--arguments"]

For example:

        "LlvmProgramTest.FullPipeline": [["cpp", "aot", "llvm", "kernel_aot_test1.py"], "--arch=cpu"]

The temporary directory where serialized cache file stays will be generated by run_tests.py. Both python program and C++ tests receives this directory path via environment variable "TAICHI_AOT_FOLDER_PATH".

For each AOT test, run_tests.py will first run the python program specified by "python_program_path" with designated arguments, followed by execution of the corresponding C++ test named "cpp_test_name".
"""
    print(message)


# Helper functions
def verify_image(image,
                 image_name,
                 tolerance=0.1,
                 regerate_groundtruth_images=False):
    if regerate_groundtruth_images:
        ground_truth_name = f"tests/python/expected/{image_name}.png"
        ti.tools.imwrite(image, ground_truth_name)
    else:
        ground_truth_name = str(pathlib.Path(
            __file__).parent) + f"/python/expected/{image_name}.png"
        ground_truth_np = ti.tools.imread(ground_truth_name)

        # TODO:Fix this on Windows
        with NamedTemporaryFile(suffix='.png') as fp:
            actual_name = fp.name

        ti.tools.imwrite(image, actual_name)
        actual_np = ti.tools.imread(actual_name)

        assert len(ground_truth_np.shape) == len(actual_np.shape)
        for i in range(len(ground_truth_np.shape)):
            assert ground_truth_np.shape[i] == actual_np.shape[i]

        diff = ground_truth_np - actual_np
        mse = np.mean(diff * diff)
        assert mse <= tolerance  # the pixel values are 0~255

        if os.path.isfile(actual_name):
            os.remove(actual_name)


def get_rel_eps():
    arch = ti.lang.impl.current_cfg().arch
    if arch == ti.opengl:
        return 1e-3
    if arch == ti.metal:
        # Debatable, different hardware could yield different precisions
        # On AMD Radeon Pro 5500M, 1e-6 works fine...
        # https://github.com/taichi-dev/taichi/pull/1779
        return 1e-4
    return 1e-6


def mkdir_p(dir_path):
    '''Creates a directory. equivalent to using mkdir -p on the command line'''

    try:
        os.makedirs(dir_path)
    except OSError as exc:  # Python > 2.5
        if exc.errno == EEXIST and os.path.isdir(dir_path):
            pass
        else:
            raise


def approx(expected, **kwargs):
    '''Tweaked pytest.approx for OpenGL low precisions'''
    class boolean_integer:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return bool(self.value) == bool(other)

        def __ne__(self, other):
            return bool(self.value) != bool(other)

    if isinstance(expected, bool):
        return boolean_integer(expected)

    kwargs['rel'] = max(kwargs.get('rel', 1e-6), get_rel_eps())

    import pytest  # pylint: disable=C0415
    return pytest.approx(expected, **kwargs)


def allclose(x, y, **kwargs):
    '''Same as: x == approx(y, **kwargs)'''
    return x == approx(y, **kwargs)


def make_temp_file(*args, **kwargs):
    '''Create a temporary file'''

    fd, name = mkstemp(*args, **kwargs)
    os.close(fd)
    return name


class TestParam:
    def __init__(self, value, required_extensions):
        self._value = value
        self._required_extensions = required_extensions

    def __repr__(self):
        return f'Param({self._value}, {self._required_extensions})'

    @property
    def value(self):
        return self._value

    @property
    def required_extensions(self):
        return self._required_extensions


if os.environ.get('TI_LITE_TEST', ''):
    _test_features = {}
else:
    _test_features = {
        # "dynamic_index": [TestParam(True, [])]
    }


def test(arch=None, exclude=None, require=None, **options):
    """
    Performs tests on archs in `expected_archs()` which are in `arch` and not in `exclude` and satisfy `require`
.. function:: ti.test(arch=[], exclude=[], require=[], **options)

    :parameter arch: backends to include
    :parameter exclude: backends and platforms to exclude
    :parameter require: extensions required
    :parameter options: other options to be passed into ``ti.init``

    """
    def exclude_arch_platform(arch, system, exclude):
        # Preprocess exclude
        if exclude is None:
            exclude = []
        if not isinstance(exclude, (list, tuple)):
            exclude = [exclude]

        for pair in exclude:
            exclude_arch = None
            exclude_sys = None
            if isinstance(pair, (list, tuple)):
                if len(pair) == 1:
                    # exclude = [(vulkan), ...]
                    exclude_arch = pair[0]
                else:
                    # exclude = [(vulkan, Darwin), ...]
                    assert len(pair) == 2
                    exclude_arch = pair[0]
                    exclude_sys = pair[1]
            else:
                # exclude = [vulkan, cpu, ...]
                exclude_arch = pair

            assert (exclude_arch is not None) or (exclude_sys is not None)
            if exclude_arch and exclude_sys:
                if exclude_arch == arch and exclude_sys == system:
                    return True
            elif exclude_arch and exclude_arch == arch:
                return True
            elif exclude_sys and exclude_sys == system:
                return True

        return False

    if arch is None:
        arch = []
    if require is None:
        require = []
    if not isinstance(arch, (list, tuple)):
        arch = [arch]
    if not isinstance(require, (list, tuple)):
        require = [require]
    archs_expected = expected_archs()
    if len(arch) == 0:
        arch = archs_expected
    else:
        arch = [v for v in arch if v in archs_expected]

    marks = []  # A list of pytest.marks to apply on the test function
    if len(arch) == 0:
        marks.append(pytest.mark.skip(reason='No supported archs'))
    else:
        arch_params_sets = [arch, *_test_features.values()]
        # List of (arch, options) to parametrize the test function
        parameters = []
        for req_arch, *req_params in itertools.product(*arch_params_sets):
            if req_arch not in arch:
                continue

            curr_system = platform.system()
            if exclude_arch_platform(req_arch, curr_system, exclude):
                continue

            if not all(
                    _ti_core.is_extension_supported(req_arch, e)
                    for e in require):
                continue

            current_options = copy.deepcopy(options)
            for feature, param in zip(_test_features, req_params):
                value = param.value
                required_extensions = param.required_extensions
                if current_options.setdefault(feature, value) != value or any(
                        not _ti_core.is_extension_supported(req_arch, e)
                        for e in required_extensions):
                    break
            else:  # no break occurs, required extensions are supported
                parameters.append((req_arch, current_options))

        if not parameters:
            marks.append(
                pytest.mark.skip(
                    reason='No all required extensions are supported'))
        else:
            marks.append(
                pytest.mark.parametrize(
                    "req_arch,req_options",
                    parameters,
                    ids=[
                        f"arch={arch.name}-{i}"
                        if len(parameters) > 1 else f"arch={arch.name}"
                        for i, (arch, _) in enumerate(parameters)
                    ]))

    def decorator(func):
        func.__ti_test__ = True  # Mark the function as a taichi test
        for mark in reversed(marks):  # Apply the marks in reverse order
            func = mark(func)
        return func

    return decorator


__all__ = [
    'test',
]
