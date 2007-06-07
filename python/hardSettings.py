
TSIZE=1024 # total texture size
MAX_TSIZE= 4096 #2048 # MAX texture size

N_VIEW_DIR=128

SHADOWMAP_SIZE=1024  # texture size for shadowmap
AOSM_SIZE=256        # texture size for shadowmmaps for AO comp[utation

# if true, use double ShadomMap optimization
doubleSM=1

NVIDIA_PATCH = 0

MOVING_QUALITY=100
STILL_QUALITY=200

SNAP_SIZE=1024   # snapshots size
SNAP_ANTIALIAS=1

names= ["favoured texture size for molecule",
  "maximal texture size (used when molecule too large for TSIZE)",
  "number of view directions ussed in AO computation",
  "texture size for shadowmap",
  "texture size for shadowmmaps for AO computation",
  "Quality of image on screen when molecole moves (between 50..200)",
  "Quality of image on screen when molecole is still (between 50..200)",
  "if 1, use double ShadomMap optimization (two way lights)",
  "use 1 - *AND* disable doubleSM - to patch a bug reported on some Nvidia cards (warning: lowers visual quality!)",
  "snapshots resolution (per side)",
  "if 1, antialias exported snapshots"]
