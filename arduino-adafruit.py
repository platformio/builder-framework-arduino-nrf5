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

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
variant = board.get("build.variant")

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoadafruitnordicnrf5")
assert isdir(FRAMEWORK_DIR)

core_path = join(FRAMEWORK_DIR, "cores", board.get("build.core"))
rtos_path = join(core_path, "freertos")
nordic_path = join(core_path, "nordic")

nrf_flags = [
    core_path,
    join(core_path, "cmsis", "include"),
    nordic_path,
    join(nordic_path, "nrfx"),
    join(nordic_path, "nrfx", "hal"),
    join(nordic_path, "nrfx", "mdk"),
    join(nordic_path, "nrfx", "soc"),
    join(nordic_path, "nrfx", "drivers", "include"),
    join(nordic_path, "softdevice", "{0}_nrf52_{1}_API".format(board.get("build.softdevice.sd_name"), board.get("build.softdevice.sd_version")), "include"),
    join(rtos_path, "Source", "include"),
    join(rtos_path, "config"),
    join(rtos_path, "portable", "GCC", "nrf52"),
    join(rtos_path, "portable", "CMSIS", "nrf52"),
    join(core_path, "sysview", "SEGGER"),
    join(core_path, "sysview", "Config"),
    join(core_path, "usb"),
    join(core_path, "usb", "tinyusb", "src"),
    join(core_path, "cmsis", "include")
]

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
        # For compatibility with sketches designed for AVR@16 MHz (see SPI lib)
        ("F_CPU", board.get("build.f_cpu")),
        "ARDUINO_ARCH_NRF5",
        "NRF5",
        board.get("build.softdevice.sd_name")
    ],

    LIBPATH=[
        join(core_path, "linker")
    ],

    CPPPATH=nrf_flags,

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
softdevice_name = board.get("build.softdevice.sd_name")

if softdevice_name:

    env.Append(
        CPPDEFINES=["%s" % softdevice_name.upper()]
    )

    hex_path = join(FRAMEWORK_DIR, "bootloader", board.get("build.variant"))

    for f in listdir(hex_path):
        if f == "{0}_bootloader-{1}_{2}_{3}.hex".format(variant, board.get("build.softdevice.version"), board.get("build.softdevice.sd_name"), board.get("build.softdevice.sd_version")):
            env.Append(SOFTDEVICEHEX=join(hex_path, f))

    if "SOFTDEVICEHEX" not in env:
        print("Warning! Cannot find an appropriate softdevice binary!")

    # Update linker script:
    ldscript_dir = join(core_path, "linker")
    mcu_family = board.get("build.mcu")
    ldscript_path = ""
    for f in listdir(ldscript_dir):
        if f.startswith(mcu_family) and softdevice_name in f.lower():
            ldscript_path = join(ldscript_dir, f)

    if ldscript_path:
        env.Replace(LDSCRIPT_PATH=ldscript_path)
    else:
        print("Warning! Cannot find an appropriate linker script for the "
              "required softdevice!")

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