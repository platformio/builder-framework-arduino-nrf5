# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.
"""

from os import listdir
from os.path import isdir, join

from SCons.Script import DefaultEnvironment
from adafruit import AdafruitBuilder
from pio import PioBuilder

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
variant = board.get("build.variant")

build_flags = " ".join(env.Flatten(env.get("BUILD_FLAGS", [])))

# if specified, use the appropriate builder
if ("BSP=ADAFRUIT" in build_flags):
    FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoadafruitnordicnrf5")
    assert isdir(FRAMEWORK_DIR)
    builder = AdafruitBuilder(env, FRAMEWORK_DIR, platform, board, variant)
elif ("BSP=SANDEEP" in build_flags):
    FRAMEWORK_DIR = platform.get_package_dir("framework-arduinonordicnrf5")
    assert isdir(FRAMEWORK_DIR)
    builder = PioBuilder(env, FRAMEWORK_DIR, platform, board, variant)
elif (variant.startswith("feather_nrf")):
    FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoadafruitnordicnrf5")
    assert isdir(FRAMEWORK_DIR)
    builder = AdafruitBuilder(env, FRAMEWORK_DIR, platform, board, variant)
else:
    FRAMEWORK_DIR = platform.get_package_dir("framework-arduinonordicnrf5")
    assert isdir(FRAMEWORK_DIR)
    builder = PioBuilder(env, FRAMEWORK_DIR, platform, board, variant)

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=["-std=gnu11"],

    CCFLAGS=[
        "-Os",  # optimize for size
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-mthumb",
        "-nostdlib",
        "--param", "max-inline-insns-single=500"
    ],

    CXXFLAGS=[
        "-fno-rtti",
        "-fno-exceptions",
        "-std=gnu++11",
        "-fno-threadsafe-statics"
    ],

    CPPDEFINES=[
        ("ARDUINO", 10805),
        ("F_CPU", board.get("build.f_cpu")),
        "ARDUINO_ARCH_NRF5",
        "NRF5"
    ],

    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections,--relax",
        "-mthumb",
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-Wl,--check-sections",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--warn-section-align"
    ],

    LIBSOURCE_DIRS=[join(FRAMEWORK_DIR, "libraries")],

    LIBS=["m"]
)

builder.add_cppdefines()
builder.add_libpath()
builder.add_cpppath()

if "BOARD" in env:
    env.Append(
        CCFLAGS=[
            "-mcpu=%s" % env.BoardConfig().get("build.cpu")
        ],
        LINKFLAGS=[
            "-mcpu=%s" % env.BoardConfig().get("build.cpu")
        ]
    )

if board.get("build.cpu") == "cortex-m4":
    env.Append(
        CCFLAGS=[
            "-mfloat-abi=softfp",
            "-mfpu=fpv4-sp-d16"
        ]
    )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:],
    CPPDEFINES=["%s" % board.get("build.mcu", "")[0:5].upper()]
)

# Process softdevice options
builder.process_softdevice()

cpp_defines = env.Flatten(env.get("CPPDEFINES", []))

# Select crystal oscillator as the low frequency source by default
clock_options = ("USE_LFXO", "USE_LFRC", "USE_LFSYNT")
if not any(d in clock_options for d in cpp_defines):
    env.Append(CPPDEFINES=["USE_LFXO"])

#
# Target: Build Core Library
#

libs = []

if "build.variant" in board:
    env.Append(CPPPATH=[
        join(FRAMEWORK_DIR, "variants", board.get("build.variant"))
    ])

    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "FrameworkArduinoVariant"),
            join(FRAMEWORK_DIR, "variants",
                 board.get("build.variant"))))

libs.append(
    env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkArduino"),
        join(FRAMEWORK_DIR, "cores", board.get("build.core"))))

env.Prepend(LIBS=libs)
