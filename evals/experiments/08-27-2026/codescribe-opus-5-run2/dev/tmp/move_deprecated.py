import shutil

moves = [
    ("software/mcfm/src/Mods/types_mod.f",
     "software/mcfm/src/Mods/deprecated/types_mod.f"),
    ("software/mcfm/src/Mods/mod_qcdloop_c.f",
     "software/mcfm/src/Mods/deprecated/mod_qcdloop_c.f"),
]

for src, dst in moves:
    shutil.move(src, dst)
    print("moved %s -> %s" % (src, dst))
