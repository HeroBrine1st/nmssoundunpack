#!/usr/bin/env python
import os
from distutils.core import setup

# https://stackoverflow.com/a/53069528\
lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = lib_folder + '/requirements.txt'
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()

setup(
    name="nmssoundunpack",
    version="1.0",
    description="Automatically unpack, convert and catalog No Man's Sky sound assets",
    author="HeroBrine1st Erquilenne",
    url="https://github.com/HeroBrine1st/nmssoundunpack",
    packages=["nmssoundunpack"],
    install_requires=install_requires,
    package_data={
        "nmssoundunpack": [
            "tools/ww2ogg/COPYING",
            "tools/ww2ogg/packed_codebooks.bin",
            "tools/ww2ogg/packed_codebooks_aoTuV_603.bin",
            "tools/ww2ogg/ww2ogg.exe",
            "tools/psarc.exe",
            "tools/revorb.exe"
        ]
    },
    scripts=['bin/unpack-nms-sound'],
)
