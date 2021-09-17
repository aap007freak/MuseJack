
#setup logging
import logging

logging.basicConfig(level=logging.INFO)
Log = logging.getLogger(__name__)


if __name__ == "__main__":
    Log.info("Starting MuseJack")
    try:
        import jack
    except OSError:
        Log.error("Couldn't load JACK audio connection kit. Make sure it is installed!")
        quit()
    Log.info("Jack audio connection kit found succesfully")
    import jacktest



