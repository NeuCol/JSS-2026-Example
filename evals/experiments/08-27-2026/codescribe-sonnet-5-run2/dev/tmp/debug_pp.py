with open("software/mcfm/src/Mods/pp_mod.f90") as f:
    text = f.read()
idx = text.find("reshape")
print(repr(text[idx:idx+120]))
print(text.count("(/"))
print(text.count("/)"))
