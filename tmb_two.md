---
layout: page
title: toddlerMusicBox Two
order: 20
---

![]({{ site.url }}/assets/images/tmb_02_002.JPG)
![]({{ site.url }}/assets/images/tmb_02_001.JPG)
![]({{ site.url }}/assets/images/tmb_02_003.JPG)
![]({{ site.url }}/assets/images/tmb_02_004.JPG)
![]({{ site.url }}/assets/images/tmb_02_005.JPG)

# Parts
* Magnat Edition 102 - 2 Wege Koax Speaker 10 cm
* [Raspberry Pi Model B+](http://www.raspberrypi.org/products/model-b-plus/)
* [STM32F4DISCOVERY](http://www.st.com/web/catalog/tools/FM116/SC959/SS1532/PF252419?sc=internet/evalboard/product/252419.jsp)
* Neuftech Mifare RC522 IC Card RFID RFID Module
* [SparkFun Voltage-Level Translator](https://github.com/sparkfun/TXB0104_breakout)
* 6 [ NeoPixel Diffused 8mm Through-Hole LED](http://www.adafruit.com/products/1734)
* 6 [Arcade LED push buttons](http://stores.ebay.de/arcadier?_trksid=p2047675.l2563)
* 49 [Adafruit NeoPixel Digital RGB LED Strip - White 60 LED](https://www.adafruit.com/products/1138)
* Massefilter Monacor FGA-30M
* 300 Mbit/s USB WLAN Stick
* LEICKE LCD TFT monitor power supply 12V 3A 5,5*2,5mm
* DEOK 12V Digital-Amplifier DC 11-14.5V 2-Channel Audio
* USB Sound Card
* NFC Tags
* some USB and HDMI adapter and cables

# Assembly
![]({{ site.url }}/assets/images/tmb_02_006.jpg)
![]({{ site.url }}/assets/images/tmb_02_007.jpg)
![]({{ site.url }}/assets/images/tmb_02_008.jpg)
![]({{ site.url }}/assets/images/tmb_02_009.jpg)

This time I used a STM32F4DISCOVERY board to drive the led strip and button lights. It is connected to one of the USB ports to the Raspberry PI. The toodlerMusicBox software send some basic commands to adjust effects and request the RFID id. The RFID reader is connected to the DISCOVERY too. The [firmware project](https://github.com/janfietz/toddlerMusicBoxControl) is hosted on Github.
