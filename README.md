# Archived
NMS internal assets are severely changed, meaning cataloging code requires the same severe changes, and I have no time (rather motivation) to analyze changes and reimplement it. Also it means dropping backwards compatibility.

The code is actual as of January 2023 (tested as important part of development). You can still use it for pre-Endurance (not tested), NEXT (tested) and Legacy (tested).

# No Man's Sky Sound Unpacker
Automatically unpack, convert and catalog No Man's Sky sound assets

# Installation

1. Install Git
2. Run ``pip install git+https://github.com/HeroBrine1st/nmssoundunpack.git``
3. Install wine to your system unless you're windows fan.

# Usage

Run ``unpack-nms-sound --help`` to view help

Example command: ``unpack-nms-sound --source "path/to/installation/No Man's Sky/GAMEDATA/PCBANKS" --destination NMSAudio``.
