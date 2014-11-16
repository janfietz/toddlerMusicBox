# Author: Jan Fietz (janfietz@gmail.com)
from setuptools import setup

setup(name = 'toddlerMusicBox',
	version = '0.0.1',
	author = 'Jan Fietz',
	author_email = 'janfietz@gmail.com',
	description = 'Raspberry Pi based music box.',
	packages=['toddlermusicbox'],
	url = 'https://github.com/janfietz/toddlerMusicBox.git',
	requires = ['neopixel', 'numpy', 'mpd'],
	scripts=['bin/toddlermusicbox']
)
