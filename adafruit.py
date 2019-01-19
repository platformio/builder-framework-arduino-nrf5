class AdafruitBuilder:
  def __init__(self, env, frameworkDir, platform, board, variant):
    self.env = env
    self.frameworkDir = frameworkDir
    self.platform = platform
    self.board = board
    self.variant = variant

    self.core_path = join(self.frameworkDir, "cores", board.get("build.core"))
    self.rtos_path = join(self.core_path, "freertos")
    self.nordic_path = join(self.core_path, "nordic")

    self.nrf_flags = [
        self.core_path,
        join(self.core_path, "cmsis", "include"),
        self.nordic_path,
        join(self.nordic_path, "nrfx"),
        join(self.nordic_path, "nrfx", "hal"),
        join(self.nordic_path, "nrfx", "mdk"),
        join(self.nordic_path, "nrfx", "soc"),
        join(self.nordic_path, "nrfx", "drivers", "include"),
        join(self.nordic_path, "softdevice", "{0}_nrf52_{1}_API".format(self.board.get("build.softdevice.sd_name"), self.board.get("build.softdevice.sd_version")), "include"),
        join(self.rtos_path, "Source", "include"),
        join(self.rtos_path, "config"),
        join(self.rtos_path, "portable", "GCC", "nrf52"),
        join(self.rtos_path, "portable", "CMSIS", "nrf52"),
        join(self.core_path, "sysview", "SEGGER"),
        join(self.core_path, "sysview", "Config"),
        join(self.core_path, "usb"),
        join(self.core_path, "usb", "tinyusb", "src"),
        join(self.core_path, "cmsis", "include")
    ]

  def add_cppdefines(self):
    self.env.Append(
      CPP_DEFINES=[
        board.get("build.softdevice.sd_name")
      ]
    )

  def add_libpath(self):
    self.env.Append(
      LIBPATH=[
        join(self.core_path, "linker")
      ]
    )
  
  def add_cpppath(self):
    self.env.append(
      CPPPATH=self.nrf_flags
    )
  
  def process_softdevice(self):
    softdevice_name = self.board.get("build.softdevice.sd_name")

    if softdevice_name:
      self.env.Append(
          CPPDEFINES=["%s" % softdevice_name.upper()]
      )

      hex_path = join(self.frameworkDir, "bootloader", self.board.get("build.variant"))

      for f in listdir(hex_path):
          if f == "{0}_bootloader-{1}_{2}_{3}.hex".format(self.variant, self.board.get("build.softdevice.version"), self.board.get("build.softdevice.sd_name"), self.board.get("build.softdevice.sd_version")):
              env.Append(SOFTDEVICEHEX=join(hex_path, f))

      if "SOFTDEVICEHEX" not in env:
          print("Warning! Cannot find an appropriate softdevice binary!")

      # Update linker script:
      ldscript_dir = join(self.core_path, "linker")
      mcu_family = self.board.get("build.mcu")
      ldscript_path = ""
      for f in listdir(ldscript_dir):
          if f.startswith(mcu_family) and softdevice_name in f.lower():
              ldscript_path = join(ldscript_dir, f)

      if ldscript_path:
          self.env.Replace(LDSCRIPT_PATH=ldscript_path)
      else:
          print("Warning! Cannot find an appropriate linker script for the "
                "required softdevice!")

  