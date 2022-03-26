#!/usr/bin/env python
from distutils.core import setup

setup(
    name="nmssoundunpack",
    version="1.0",
    description="Automatically unpack, convert and catalog No Man's Sky sound assets",
    author="HeroBrine1st Erquilenne",
    url="https://github.com/HeroBrine1st/nmssoundunpack",
    packages=["nmssoundunpack"],
    requires=["rich", "xmltodict"],
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
