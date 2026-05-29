# What is this
I wanted to write MIDI files and existing tools weren't doing it for me so I did it myself. So: a MIDI tracker. It's built to make MIDI files. However, it's not a general MIDI editor.

# Playback
TMidiTracker operates purely in MIDI — it technically has no audio output of its own. You will need a MIDI device/software that supports General Midi in order to use this.

On Windows, Microsoft GS Wavetable Synth will be available, so no extra work is needed.

Fluidsynth is a recommended software if you don't have anything else preferred. The tracker also has integration with it, and will provide built in audio
if Fluidsynth is detected on the system. (TODO: does this work on not Linux?)

# Installation
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
    - I'm pretty sure what's happening here is there isn't a binary available, so it has to build it, and these are the tools it needs to do so.
## Windows
- Install Python (built with 3.13.5, should work with newer)
- Download and extract repository wherever you feel like.
- Launch run.bat
  - This is how you launch the program. It will setup venv and install dependencies the first time around.<br>(Delete the 'INSTALLED' file that gets generated to redo this)
## Other
- I haven't got around to that yet. Should be the same process, but you'll have to do what run.bat does manually. Also the program may still not work because it's untested elsewhere.

## Optional Dependencies
- Fluidsynth.
  - This will allow the program to produce audio on its own, rather than needing a standalone device.
  - If integration is working, there will be a port labeled "Internal Fluidsynth".
  - Options related to Fluidsynth will also be exposed.

# Uninstallation
Delete the program folder.