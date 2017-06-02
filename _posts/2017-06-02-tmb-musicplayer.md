---
layout: post
title: toddlerMusicBox Musicplayer
excerpt_separator: <!--more-->
---

After building tmb One and Two I was thinking about what could be done better. One main concern I had was the booting time of the RaspberryPi. I wanted to have an immediate response after power button was switched on. So I started the tmb Musicplayer project which is a custom board and custom software. I used assembled a dev board with a DiscoveryF4 and MP3 decoder Arduino shield.
![]({{ site.url }}/assets/images/tmb_mp_devboard.jpg)
<!--more-->

This test setup was my development platform for a custom [firmware project](https://github.com/janfietz/tmb_musicplayer). I tried to port the main features of a toddler music box to this concept board. I used the STM32F4 port [ChibiOS](http://www.chibios.org) to develop drivers for the MFRC522 RFID chip, WS2811 LED and VLSI 1053 mp3 decoder chip.

After finishing a basic software which played music files from SD card I started to use [KiCad](http://kicad-pcb.org/) to layout a pcb. The manufactored pcb was delivered to me in the beginning of 2017.
![]({{ site.url }}/assets/images/tmb_mp_pcb.jpg)

It took some while to assemble the parts because there where some other projects on my list. In may 2017 a running version was finished.
<iframe width="560" height="315" src="https://www.youtube.com/embed/TigDNIEKAd4" frameborder="0" allowfullscreen></iframe>

Currently I am working again to get the software finished.
