from enum import Enum, auto
from threading import Thread

import cv2.cv2 as cv2


class State(Enum):
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2


def realtime(f):
    return f


class AbstractPlayer(Thread):
    """
    Helper class to abstract some of the Logic
    """

    def __init__(self, total_frames, frame_rate=60, jack_frame_rate=44100):

        super().__init__(target=self.loop)
        self.total_frames = total_frames

        self.jack_frame_rate = jack_frame_rate
        self.frame_rate = frame_rate

        self.jack_frames_per_frame = jack_frame_rate / frame_rate

        self.on_frame = 0
        self.previous_frame = None

        # flags
        self.status = State.PAUSED
        self.frame_requested = False
        self.seek_requested = -1

    def frame(self):
        pass  # this should be implemented by child classes

    def pause_frame(self):
        pass

    def loop(self):
        while True:
            if self.frame_requested and (not self.status is State.STOPPED):
                self.frame_requested = False

                # check if a seek was requested
                seek_to = self.seek_requested
                if seek_to != -1:
                    self.on_frame = seek_to  # if seek requested, set on_frame to the requested seek
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
    def seek(self, jack_frame):
        self.seek_requested = jack_frame / self.jack_frames_per_frame
        self.frame_requested = True
        self.play() # if seeking, automatically start playing

    def pause(self):
        self.status = State.PAUSED

    def play(self):
        self.status = State.PLAYING

    def stop(self):
        self.status = State.STOPPED


class Video(AbstractPlayer):

    def __init__(self, video_file_name, jack_frame_rate=44100):

        self.vcap = cv2.VideoCapture(video_file_name)

        super().__init__(frame_rate=round(self.vcap.get(cv2.CAP_PROP_FPS)),
                         total_frames=round(self.vcap.get(cv2.CAP_PROP_FRAME_COUNT)),
                         jack_frame_rate=jack_frame_rate)

        # we keep the last frame drawn in memory for pausing
        self.last_frame = None

        # we always need to call this start loop at the end of the __init__ method
        self.start()

    def seek(self, jack_frame):
        # we override the seek method, to be able to tell cv2 that we switched frame order
        super().seek(jack_frame)
        self.vcap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_requested)

    def frame(self):
        print("called 60 times a second")
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
