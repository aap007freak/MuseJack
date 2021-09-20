import os
import shutil
import sys

import logging
from pathlib import Path

from musejack import util
from musejack.util import resource_path

if "--debug" in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
Log = logging.getLogger(__name__)


if __name__ == "__main__":
    Log.info("Starting MuseJack")

    try:
        import jack
    except OSError:
        Log.error("Couldn't load JACK audio connection kit. Make sure it is installed!")
        quit()
    Log.info("JACK audio connection kit found succesfully")

    #todo this is OC specific
    prefs = util.load_musescore_ini(Path("C:\\Users\\Anton\\AppData\\Roaming\\MuseScore\\musescore3.ini"))

    Log.info("Found musescore3.ini file succesfully")

    #check if the preferences are setup correctly
    if not prefs.get("jack\\useJackAudio") == "true"\
            or not prefs.get("jack\\useJackMIDI") == "true"\
            or not prefs.get("jack\\useJackTransport") == "true":
        Log.warning("Jack settings in Musescore are faulty! Ensure you have enabled Jack audio & Jack transport in "
                    "Preferences > IO")
        #todo, we can add those values manually, but should we?
    else:
        Log.info("Jack settings in Musescore OK")

    plugins_dir = prefs.get("paths\\myPlugins")
    plugin = Path(plugins_dir).joinpath("musejack_plugin.qml")

    if not plugin.exists():
        Log.warning(f"Musejack plugin not found! Adding it in folder {plugins_dir}")
        shutil.copy2(resource_path("musejackplugin.qml"), plugins_dir)
    else:
        Log.info("Musejack plugin found succesfully")

    #initiating client
    @jack.set_error_function
    def error(msg):
        Log.warning(f"Jack Error: {msg}")


    @jack.set_info_function
    def info(msg):
        Log.info(f"Jack Info: {msg}")


    client = jack.Client('MuseJack')

    if client.status.server_started:
        Log.info(f"JACK server was not running, so started a new one: {client.name}")
    else:
        Log.info(f"JACK server was already running: {client.name}")
    if client.status.name_not_unique:
        print(f"unique client name generated: {client.name}")


    @client.set_shutdown_callback
    def shutdown(status, reason):
        Log.error('JACK shutdown!')
        Log.error('status:', status)
        Log.error('reason:', reason)
        quit()


    @client.set_blocksize_callback
    def blocksize(blocksize):
        pass # this should


    @client.set_samplerate_callback
    def samplerate(samplerate):
        pass


    @client.set_xrun_callback
    def xrun(delay):
        Log.debug('xrun; delay', delay, 'microseconds')

    players = []

    current_state = -1
    @client.set_timebase_callback
    def callback(state: int, blocksize: int, position, new_pos: bool) -> None:
        global current_state
        if state != current_state:
            # if the new state is the rolling state, start the video
            Log.debug(f"new state {state}")
            if state == jack.ROLLING:
                Log.debug(f"seeking to audio frame {position.frame}")
                for player in players:
                    player._seek(position.frame)

            current_state = state

        for player in players:
            player._step()

    Log.info("activating JACK")
    try:
        with client:
            # add ourselves to every target port
            target_ports = client.get_ports(
                is_physical=True, is_input=True, is_audio=True)
            if len(client.outports) == 1 and len(target_ports) > 1:
                # Connect mono file to stereo output
                client.outports[0].connect(target_ports[0])
                client.outports[0].connect(target_ports[1])
            else:
                for source, target in zip(client.outports, target_ports):
                    source.connect(target)
            input()
    except Exception as e:
        print(e)









