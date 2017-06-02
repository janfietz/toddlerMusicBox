---
layout: page
title: About
order: 10
---
My toddler is currently one and a half and loves music. My wife and I decided to search for a music playback solution for him. Our first idea was to buy a cd player radio. After my own experience of listening to mp3's for many years I did not want to use CDs anymore. For a short test if let my toddler play with my ipod but he was not able to select his favorite music. Inspired by some other projects I came up with the idea for a custom made music box for him.

# Operating System
The Pi is running an [archlinux](http://archlinuxarm.org/platforms/armv6/raspberry-pi). I installed Python 2.7 with some extensions and the [Music Player Daemon](http://www.musicpd.org/).

# Code
It's a Python based project. I created a modular architecture and some of the system parameters are configurable using a config script. It should be possible to use this code with another count of LED or buttons.

# Conclusion
I was pretty surprised how easy it was for my toddler to put the NFC-cards into the slot. He was able to select the next title and adjust the volume.

# Acknowledgments
I was inspired by the [Song Blocks Project](http://shawnrk.github.io/songblocks/).
The interface for MPD was inspired by [ncmpy](https://github.com/cykerway/ncmpy).
