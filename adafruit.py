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

import re

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
variant = board.get("build.variant")

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoadafruitnrf52")
assert isdir(FRAMEWORK_DIR)

CORE_DIR = join(FRAMEWORK_DIR, "cores", board.get("build.core"))
assert isdir(CORE_DIR)

NORDIC_DIR = join(CORE_DIR, "nordic")
assert isdir(NORDIC_DIR)

default_bsp_version = "0.19.0"
default_softdevice_version = "6.1.1"
default_bootloader_version = "0.3.2"

# Read defaults from build.txt/platform.txt/programmers.txt
with open(join(FRAMEWORK_DIR, "platform.txt"), "r") as fp:
    for line in fp:
        match = re.search(r"^version=(\d+\.\d+.\d+)", line)
        if match:
            default_bsp_version = match.group(1)
        match = re.search(r"_bootloader-(\d+\.\d+.\d+)_", line)
        if match:
            default_bootloader_version = match.group(1)

with open(join(FRAMEWORK_DIR, "boards.txt"), "r") as fp:
    for line in fp:
        match = re.search(r"build.sd_version=(\d+\.\d+.\d+)", line)
        if match:
            default_softdevice_version = match.group(1)

bsp_version = board.get("build.bsp.version", default_bsp_version)
softdevice_version = board.get("build.softdevice.sd_version", default_softdevice_version)
bootloader_version = board.get("build.bootloader.version", default_bootloader_version)

# print(bsp_version, softdevice_version, bootloader_version)

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=["-std=gnu11"],

    CCFLAGS=[
        "-Ofast",
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
        ("F_CPU", board.get("build.f_cpu")),
        ("ARDUINO", 10804),
        "ARDUINO_ARCH_NRF52",
        ("ARDUINO_BSP_VERSION", '\\"%s\\"' % bsp_version),
        "ARDUINO_FEATHER52",
        "ARDUINO_NRF52_ADAFRUIT",
        "NRF52_SERIES",
        ("LFS_NAME_MAX", 64)
    ],

    LIBPATH=[
        join(CORE_DIR, "linker")
    ],

    CPPPATH=[
        join(CORE_DIR, "cmsis", "include"),
        join(CORE_DIR, "cmsis", "Core", "Include"),
        join(NORDIC_DIR),
        join(NORDIC_DIR, "nrfx"),
        join(NORDIC_DIR, "nrfx", "hal"),
        join(NORDIC_DIR, "nrfx", "mdk"),
        join(NORDIC_DIR, "nrfx", "soc"),
        join(NORDIC_DIR, "nrfx", "drivers", "include"),
        join(NORDIC_DIR, "nrfx", "drivers", "src")
    ],

    LINKFLAGS=[
        "-Ofast",
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
            "-mcpu=%s" % board.get("build.cpu")
        ],
        LINKFLAGS=[
            "-mcpu=%s" % board.get("build.cpu")
        ]
    )

if board.get("build.cpu") == "cortex-m4":
    env.Append(
        CCFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
            "-u", "_printf_float"
        ],
        LINKFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
            "-u", "_printf_float"
        ]
    )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:],
    CPPDEFINES=["%s" % board.get("build.mcu", "").upper()]
)

# Process softdevice options
softdevice_name = board.get("build.softdevice.sd_name")
board_name = board.get("build.bootloader.hex_filename", board.get("build.variant"))

if softdevice_name:
    env.Append(
        CPPPATH=[
            join(NORDIC_DIR, "softdevice",
                 "%s_nrf52_%s_API" % (softdevice_name, softdevice_version), "include"),
            join(NORDIC_DIR, "softdevice",
                 "%s_nrf52_%s_API" % (softdevice_name, softdevice_version), "include", "nrf52")
        ],
        CPPDEFINES=[
            softdevice_name.upper(),
            "NRF52_" + (softdevice_name.upper()),
            "SOFTDEVICE_PRESENT"
        ]
    )

    hex_path = join(FRAMEWORK_DIR, "bootloader", board_name)
    if isdir(hex_path):
        for f in listdir(hex_path):
            if f == "{0}_bootloader-{1}_{2}_{3}.hex".format(
                    variant, bootloader_version, softdevice_name, softdevice_version):
                env.Append(DFUBOOTHEX=join(hex_path, f))

    if not board.get("build.ldscript", ""):
        # Update linker script:
        ldscript_dir = join(CORE_DIR, "linker")
        ldscript_name = board.get("build.arduino.ldscript", "")
        if ldscript_name:
            env.Append(LIBPATH=[ldscript_dir])
            env.Replace(LDSCRIPT_PATH=ldscript_name)
        else:
            print("Warning! Cannot find an appropriate linker script for the "
                  "required softdevice!")

freertos_path = join(CORE_DIR, "freertos")
if isdir(freertos_path):
    env.Append(
        CPPPATH=[
            join(freertos_path, "Source", "include"),
            join(freertos_path, "config"),
            join(freertos_path, "portable", "GCC", "nrf52"),
            join(freertos_path, "portable", "CMSIS", "nrf52")
        ]
    )

sysview_path = join(CORE_DIR, "sysview")
if isdir(sysview_path):
    env.Append(
        CPPPATH=[
            join(sysview_path, "SEGGER"),
            join(sysview_path, "Config")
        ]
    )

usb_path = join(CORE_DIR, "TinyUSB")
if isdir(usb_path):
    if env.subst("$BOARD") != "adafruit_feather_nrf52832":
        env.Append(
            CPPDEFINES=[
                "USBCON",
                "USE_TINYUSB"
            ]
        )

    env.Append(
        CPPPATH=[
            usb_path,
            join(usb_path, "Adafruit_TinyUSB_ArduinoCore"),
            join(usb_path, "Adafruit_TinyUSB_ArduinoCore", "tinyusb", "src")
        ]
    )

if "build.usb_product" in env.BoardConfig():
    env.Append(
        CPPDEFINES=[
            ("USB_VID", board.get("build.hwids")[0][0]),
            ("USB_PID", board.get("build.hwids")[0][1]),
            ("USB_PRODUCT", '\\"%s\\"' % board.get("build.usb_product", "").replace('"', "")),
            ("USB_MANUFACTURER", '\\"%s\\"' % board.get("vendor", "").replace('"', ""))
        ]
    )


env.Append(
    CPPPATH=[
        join(CORE_DIR)
    ]
)

cpp_flags = env.Flatten(env.get("CPPDEFINES", []))

if "CFG_DEBUG" not in cpp_flags:
    env.Append(CPPDEFINES=[("CFG_DEBUG", 0)])

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
        join(CORE_DIR)))

env.Prepend(LIBS=libs)
