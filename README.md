# C.H.I.P.tunes

MPD display and button interface for a C.H.I.P. single-board computer.

Created using a modified version of Matt Hawkins' [16x2 LCD Module Control Using Python](http://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/) blog post.

*NOTE* in order for this code to work, please install the [Chip IO](https://github.com/xtacocorex/CHIP_IO) and [python-mpd](https://pythonhosted.org/python-mpd2/index.html) packages.

Pinout is as follows:

| LCD/button Pin | C.H.I.P. IO Pin |
| ------------- | ------------- |
| LCD_RS  | XIO-P4 |
| LCD_E  | XIO-P2  |
| LCD_D4 | XIO-P7 |
| LCD_D5 | XIO-P5 |
| LCD_D6 | XIO-P3 |
| LCD_D7 | XIO-P6 |
| display mode btn | AP-EINT3 |
| play/pause btn | XIO-P1 |
| previous track btn | AP-EINT1 |
| next track btn | XIO-P0 |

Please excuse any ugly syntax, this is my first time using python!