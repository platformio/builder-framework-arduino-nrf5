from os import listdir
from os.path import isdir, join

from SCons.Script import DefaultEnvironment

class AdafruitBuilder:
  def __init__(self, env, frameworkDir, platform, board, variant):
    self.env = env
    self.frameworkDir = frameworkDir
    self.platform = platform
    self.board = board
    self.variant = variant

    self.coreDir = join(frameworkDir, "cores", board.get("build.core")) 
    assert isdir(self.coreDir) 

    self.nordicDir = join(self.coreDir, "nordic")
    assert isdir(self.nordicDir)

    self.bsp_version = board.get("build.bsp.version", "0.9.3")
    self.softdevice_version = board.get("build.softdevice.sd_version", "6.1.1")
    self.bootloader_version = board.get("build.bootloader.version", "0.2.6") 
    self.softdevice_name = self.board.get("build.softdevice.sd_name")
    self.board_name = self.board.get("build.bootloader", self.board.get("build.variant"))

  def add_cpuflags(self):
    self.env.Append(
        CCFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
            "-u _printf_float"
        ],
        LINKFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
            "-u _printf_float"
        ]
    )

  def add_cppdefines(self):
    self.env.Append(
      CPP_DEFINES=[
        "NRF52",
        "ARDUINO_FEATHER52",
        "ARDUINO_NRF52_ADAFRUIT",
        "NRF52_SERIES",
        self.softdevice_name, 
        ("F_CPU", self.board.get("build.f_cpu"))
      ]
    )

  def add_libpath(self):
    self.env.Append(
      LIBPATH=[
        join(self.core_path, "linker")
      ]
    )
  
  def add_cpppath(self):
    self.env.Append(
      CPPPATH=[ 
        join(self.coreDir), 
        join(self.coreDir, "cmsis", "include"), 
        join(self.nordicDir), 
        join(self.nordicDir, "nrfx"), 
        join(self.nordicDir, "nrfx", "hal"), 
        join(self.nordicDir, "nrfx", "mdk"), 
        join(self.nordicDir, "nrfx", "soc"), 
        join(self.nordicDir, "nrfx", "drivers", "include"), 
      ]
    )

    self.rtosDir = join(self.coreDir, "freertos")
    if(isdir(self.rtosDir)):
      self.env.Append(
        CPPPATH=[
            join(self.rtosDir, "Source", "include"),
            join(self.rtosDir, "config"),
            join(self.rtosDir, "portable", "GCC", "nrf52"),
            join(self.rtosDir, "portable", "CMSIS", "nrf52")
        ]
    )

    self.sysviewDir = join(self.coreDir, "sysview")
    if(isdir(self.sysviewDir)):
        self.env.Append(
            CPPPATH=[
                join(self.sysviewDir, "SEGGER"),
                join(self.sysviewDir, "Config")
            ]
        )

    self.usbDir = join(self.coreDir, "usb")
    if(isdir(self.usbDir)):
        self.env.Append(
            CPPPATH=[
                join(self.usbDir),
                join(self.usbDir, "tinyusb", "src")
            ]
        )
  
  def process_softdevice(self):
    if self.softdevice_name:
      self.env.Append(
        CPPPATH=[
          join(self.nordicDir, "softdevice", "%s_nrf52_%s_API" % (self.softdevice_name, self.softdevice_version), "include") 
        ],
        CPPDEFINES=[
          "%s" % self.softdevice_name.upper(), 
          "NRF52_"+(self.softdevice_name.upper()), 
          "SOFTDEVICE_PRESENT" 
        ] 
      )

      hex_path = join(self.frameworkDir, "bootloader", self.board.get("build.variant"))

      for f in listdir(hex_path):
          if f == "{0}_bootloader-{1}_{2}_{3}.hex".format(self.variant, self.board.get("build.softdevice.version"), self.board.get("build.softdevice.sd_name"), self.board.get("build.softdevice.sd_version")):
              self.env.Append(SOFTDEVICEHEX=join(hex_path, f))

      if "SOFTDEVICEHEX" not in self.env:
          print("Warning! Cannot find an appropriate softdevice binary!")

      # Update linker script:
      ldscript_dir = join(self.core_path, "linker")
      mcu_family = self.board.get("build.mcu")
      ldscript_name = self.board.get("build.ldscript", "")
      if ldscript_name: 
            ldscript_path = join(ldscript_dir, f) 
            self.env.Append(LINKFLAGS=[ 
              "-L"+ldscript_dir,
#             "-T"+ldscript_name  
            ]) 
            self.env.Replace(LDSCRIPT_PATH=ldscript_name) 
