class NordicBuilder:
  def __init__(self, env, frameworkDir, platform, board, variant):
    self.env = env
    self.frameworkDir = frameworkDir
    self.platform = platform
    self.board = board
    self.variant = variant

  def add_cppdefines(self):
    # no additional cppdefines needed

  def add_libpath(self):
    self.env.Append(
      LIBPATH=[
        join(self.frameworkDir, "cores", self.board.get("build.core"),
             "SDK", "components", "toolchain", "gcc")
      ],
    )
  
  def add_cpppath(self):
    self.env.append(
      CPPPATH=[
        join(self.frameworkDir, "cores", self.board.get("build.core")),
        join(self.frameworkDir, "cores", self.board.get("build.core"),
             "SDK", "components", "drivers_nrf", "delay"),
        join(self.frameworkDir, "cores", self.board.get("build.core"),
             "SDK", "components", "device"),
        join(self.frameworkDir, "cores", self.board.get("build.core"),
             "SDK", "components", "toolchain"),
        join(self.frameworkDir, "cores", self.board.get("build.core"),
             "SDK", "components", "toolchain", "CMSIS", "Include")
      ]
    )
  
  def process_softdevice(self):
    softdevice_ver = None
    cpp_defines = self.env.Flatten(self.env.get("CPPDEFINES", []))
    if "NRF52_S132" in cpp_defines:
        softdevice_ver = "s132"
    elif "NRF51_S130" in cpp_defines:
        softdevice_ver = "s130"
    elif "NRF51_S110" in cpp_defines:
        softdevice_ver = "s110"

    if softdevice_ver:

        self.env.Append(
            CPPPATH=[
                join(self.frameworkDir, "cores", self.board.get("build.core"),
                    "SDK", "components", "softdevice", softdevice_ver, "headers")
            ],

            CPPDEFINES=["%s" % softdevice_ver.upper()]
        )

        hex_path = join(self.frameworkDir, "cores", self.board.get("build.core"),
                        "SDK", "components", "softdevice", softdevice_ver, "hex")

        for f in listdir(hex_path):
            if f.endswith(".hex") and f.lower().startswith(softdevice_ver):
                self.env.Append(SOFTDEVICEHEX=join(hex_path, f))

        if "SOFTDEVICEHEX" not in self.env:
            print("Warning! Cannot find an appropriate softdevice binary!")

        # Update linker script:
        ldscript_dir = join(self.frameworkDir, "cores",
                            self.board.get("build.core"), "SDK",
                            "components", "softdevice", softdevice_ver,
                            "toolchain", "armgcc")
        mcu_family = board.get("build.ldscript", "").split("_")[1]
        ldscript_path = ""
        for f in listdir(ldscript_dir):
            if f.endswith(mcu_family) and softdevice_ver in f.lower():
                ldscript_path = join(ldscript_dir, f)

        if ldscript_path:
            self.env.Replace(LDSCRIPT_PATH=ldscript_path)
        else:
            print("Warning! Cannot find an appropriate linker script for the "
                  "required softdevice!")