# Copyright 2022 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Python bindings for MuJoCo."""

import ctypes
import ctypes.util
import os
import platform
import subprocess
from typing import IO, Union
from typing_extensions import TypeAlias
import warnings
import zipfile

# Extend the path to enable multiple directories to contribute to the same
# package. Without this line, the `mujoco-mjx` package would not be able to
# be discovered by import. For more information, see: https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages
# NOTE: As per the Python Packaging User Guide linked above, the preferable way
# of declaring the namespace package is to use the native namespace packages.
# This seems non-trivial at the current state of the project, however.
# For more information, see: https://github.com/google-deepmind/mujoco/issues/2119
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

_SYSTEM = platform.system()
if _SYSTEM == 'Windows':
  ctypes.WinDLL(os.path.join(os.path.dirname(__file__), 'mujoco.dll'))
elif _SYSTEM == 'Darwin':
  proc_translated = subprocess.run(
      ['sysctl', '-n', 'sysctl.proc_translated'], capture_output=True).stdout
  try:
    is_rosetta = bool(int(proc_translated))
  except ValueError:
    is_rosetta = False
  if is_rosetta and platform.machine() == 'x86_64':
    raise ImportError(
        'You are running an x86_64 build of Python on an Apple Silicon '
        'machine. This is not supported by MuJoCo. Please install and run a '
        'native, arm64 build of Python.')

from mujoco import _specs
from mujoco._callbacks import *
from mujoco._constants import *
from mujoco._enums import *
from mujoco._errors import *
from mujoco._functions import *
from mujoco._render import *
from mujoco._specs import *
from mujoco._structs import *
from mujoco.gl_context import *
from mujoco.renderer import Renderer

MjStruct: TypeAlias = Union[
    _specs.MjsBody,
    _specs.MjsFrame,
    _specs.MjsGeom,
    _specs.MjsJoint,
    _specs.MjsLight,
    _specs.MjsMaterial,
    _specs.MjsSite,
    _specs.MjsMesh,
    _specs.MjsSkin,
    _specs.MjsTexture,
    _specs.MjsText,
    _specs.MjsTuple,
    _specs.MjsCamera,
    _specs.MjsFlex,
    _specs.MjsHField,
    _specs.MjsKey,
    _specs.MjsNumeric,
    _specs.MjsPair,
    _specs.MjsExclude,
    _specs.MjsEquality,
    _specs.MjsTendon,
    _specs.MjsSensor,
    _specs.MjsActuator,
    _specs.MjsPlugin,
]

def to_zip(spec: _specs.MjSpec, file: Union[str, IO[bytes]]) -> None:
  """Converts a spec to a zip file.

  Args:
    spec: The mjSpec to save to a file.
    file: The path to the file to save to or the file object to write to.
  """
  files_to_zip = spec.assets
  files_to_zip[spec.modelname + '.xml'] = spec.to_xml()
  if isinstance(file, str):
    directory = os.path.dirname(file)
    os.makedirs(directory, exist_ok=True)
    file = open(file, 'wb')
  with zipfile.ZipFile(file, 'w') as zip_file:
    for filename, contents in files_to_zip.items():
      zip_info = zipfile.ZipInfo(os.path.join(spec.modelname, filename))
      zip_file.writestr(zip_info, contents)

_specs.MjSpec.to_zip = to_zip

HEADERS_DIR = os.path.join(os.path.dirname(__file__), 'include/mujoco')
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), 'plugin')

PLUGIN_HANDLES = []

def _load_all_bundled_plugins():
  for directory, _, filenames in os.walk(PLUGINS_DIR):
    for filename in filenames:
      if os.path.splitext(filename)[-1] in [".dll", ".dylib", ".so"]:
        PLUGIN_HANDLES.append(ctypes.CDLL(os.path.join(directory, filename)))
      elif filename == "__init__.py":
        pass
      else:
        warnings.warn('Ignoring non-library in plugin directory: '
                      f'{os.path.join(directory, filename)}', ImportWarning)

_load_all_bundled_plugins()

__version__ = mj_versionString()  # pylint: disable=undefined-variable
