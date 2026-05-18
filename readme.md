# What is this
I wanted to write MIDI files and existing tools weren't doing it for me so I did it myself. So: a MIDI tracker. It's built to make MIDI files. However, it's not a general MIDI editor.

# Installation
## Windows
- Install Python (built with 3.13.5, should work with newer)
- Download and extract repository wherever you feel like.
- Launch run.bat
  - This is how you launch the program. It will setup venv and install dependencies the first time around.<br>(Delete the 'INSTALLED' file that gets generated to redo this)
## Linux (WIP, MAY NOT WORK)
<!-- - Install python3-tk
- Install libasound2t64 -->
- Download and extract repository wherever you feel like.
- Launch run.sh
  - This is how you launch the program. It will setup venv and install dependencies the first time around.<br>(Delete the 'INSTALLED' file that gets generated to redo this)
- Potential Errors
  - Failure when installing python-rtmidi (note, error messages are verbose for this so a sample will be provided)
    - Unknown compilers "../meson.build:1:0: ERROR: Unknown compiler(s): [['c++'], ['g++'], ['clang++'], ['nvc++'], ['pgc++'], ['icpc'], ['icpx']]"
      - Install any of those compilers
        - (It worked with clang when I tried)
    - ALSA not found `Run-time dependency alsa found: NO  (tried pkg-config)`
      - Install a suitable ALSA lib
        - `dnf install alsa-lib-devel`
        - TODO: others (i think it's libasound2?)
    - JACK not found
      - idk it stopped being annoying at me?
    - `Run-time dependency python found: NO  (tried pkgconfig and sysconfig)`
      - Install python3-devel
        - `dnf install python3-devel`
        - TODO: others (probably just on apt)
## Other
- I haven't got around to that yet. Should be the same process, but you'll have to do what run.bat does manually. Also the program may still not work because it's untested elsewhere.

# Other Information
no