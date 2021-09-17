import asyncio
import queue
from enum import Enum
from threading import Thread

import cv2.cv2 as cv2
import soundfile
from jack import Client


class State(Enum):
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2


def realtime(f):
    return f


class AbstractPlayer(Thread):
    """
    Helper class to abstract some of the player logic
    """

    def __init__(self, client: Client, total_frames, frame_rate=60):

        super().__init__(target=self.loop)

        self.client = client
        self.total_frames = total_frames

        self.jack_frame_rate = client.samplerate
        self.frame_rate = frame_rate

        self.jack_frames_per_frame = client.samplerate / frame_rate

        self.on_frame = 0
        self.previous_frame = None

        self.text = None

        # flags
        self.status = State.PAUSED
        self.frame_requested = False
        self.seek_requested = -1

    def seek(self, oldPos, newPos):
        """
        arguments both in own frames
        """
        pass

    def frame(self):
        pass  # this should be implemented by child classes

    def pause_frame(self):
        pass  # this should be implemented by child classes

    def loop(self):
        while True:
            if self.frame_requested and self.status is not State.STOPPED:
                self.frame_requested = False

                # check if a seek was requested
                if self.seek_requested != -1:
                    self.seek(self.on_frame, self.seek_requested)
                    self.on_frame = self.seek_requested  # if seek requested, set on_frame to the requested seek
                    self.seek_requested = -1
                else:
                    self.on_frame += 1  # else increment by one

                # check if we reached the end of the file
                if self.on_frame > self.total_frames:
                    self.stop()

                if self.status is State.PLAYING:
                    self.frame()
                elif self.status is State.PAUSED:
                    self.pause_frame()

    @realtime
    def _step(self, jack_frame_amount):
        if self.on_frame * self.jack_frames_per_frame < jack_frame_amount:
            self.frame_requested = True

    @realtime
    def _seek(self, jack_frame):
        self.seek_requested = round(jack_frame / self.jack_frames_per_frame)
        self.frame_requested = True
        self.play()  # if seeking, automatically start playing

    def pause(self):
        self.status = State.PAUSED

    def play(self):
        self.status = State.PLAYING

    def stop(self):
        self.status = State.STOPPED


class Audio(AbstractPlayer):

    def __init__(self, client, audio_file_name, buffer_size=20):
        # todo what if the jack samplerate isn't the same as te audio file sample rate?
        self.buffer_size = buffer_size
        self.jack_block_size = client.blocksize

        self.queue = asyncio.Queue()

        # read some data from the soundfile
        self.audio_file_name = audio_file_name

        sf = soundfile.SoundFile(self.audio_file_name)
        fr = client.blocksize * self.buffer_size / client.samplerate
        super().__init__(client=client,
                         total_frames=sf.frames,
                         frame_rate=fr)

        self.block_generator = sf.blocks(blocksize=client.blocksize,
                                         dtype="float32",
                                         always_2d=True,
                                         fill_value=0)

        # register some ports for audio
        for channel in range(sf.channels):
            client.outports.register(f'out_{channel + 1}')

        self.start()

    def seek(self, oldPos, newPos):
        pass

    def frame(self):
        data = self.block_generator.__next__()
        if data is None:
            self.stop()  # Playback is finished
        else:
            for channel, port in zip(data.T, self.client.outports):
                port.get_array()[:] = channel

    def pause_frame(self):
        pass  # do nothing on pause frame


class Video(AbstractPlayer):

    def __init__(self, client, video_file_name):

        self.vcap = cv2.VideoCapture(video_file_name)

        super().__init__(client=client, frame_rate=round(self.vcap.get(cv2.CAP_PROP_FPS)),
                         total_frames=round(self.vcap.get(cv2.CAP_PROP_FRAME_COUNT)), )

        # we keep the last frame drawn in memory for pausing
        self.last_frame = None

        # we always need to call this start loop at the end of the __init__ method
        self.start()

    def seek(self, oldPos, newPos):
        self.vcap.set(cv2.CAP_PROP_POS_FRAMES, newPos)

    def frame(self):
        ret, frame = self.vcap.read()
        if ret:
            # Display the resulting frame
            if self.text:
                self.text.draw(frame)

                if self.text.done():
                    self.text = None

            frameS = cv2.resize(frame, (480, 360), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            cv2.imshow("output", frameS)

            # save the frame
            self.last_frame = frameS
            if cv2.waitKey(1):  # we need this for
                return

    def pause_frame(self):
        if self.last_frame:
            cv2.imshow("output", self.last_frame)

            if cv2.waitKey(1):  # we need this for
                return

    def stop(self):
        self.vcap.release()
        cv2.destroyAllWindows()
