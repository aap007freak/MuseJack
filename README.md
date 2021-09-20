# MuseJack

MuseJack is an add-on plugin and standalone program for Musescore that allows video files to be synced with Musescore scores.
 It facilitates easier film scoring and similar endeavours.

## Installation
**Warning**! MuseJack is currently in *alpha,* there will be new breaking features all the time, and expect bugs!

1. Download and install [JACK audio connection kit](https://jackaudio.org/downloads/) for your operating system.
2. Download the most recent executable from the [Releases](https://github.com/aap007freak/MuseJack/releases) page.
3. Open Musecore, go into Preferences > I/O and make sure to enable the JACK audio server, including all the options
 **except timebase master**.
4. Run the MuseJack executable and point it to *.mjck* file (see below). 

## Usage

### MuseJack Musescore Plugin
MuseJack is a standalone program that runs alongside Musescore. To know which video files to sync to which parts of the score 
and the exact timings, MuseJack needs files ending in *.mjck*. You can create these manually, but the preferred way 
to generate them is using the MuseJack Musescore Plugin. MuseJack will automatically try to install this Musescore plugin
when you first run the program. 
 
Check if the plugin is installed correctly by navigating to Plugins > Plugin Manager...


Here you can also assign a shortcut to the plugin, which is higly recommended.


Running the plugin (by clicking on the name in the menu or activating the shortcut), will generate a .mjck file in the
same directory as the score. You can then point MuseJack to read the .mjck file and the correct video file(s) should be syncing!

### An Example .mjck file


## Contributing

MuseJack is built using Python 3.9 with [poetry](https://python-poetry.org/). To build:
```bash
git clone https://github.com/aap007freak/MuseJack
cd MuseJack
poetry install
# then
poetry run python musejack/main.py
```
