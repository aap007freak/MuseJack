# !/usr/bin/env python3

"""Create a JACK client that prints a lot of information.
This client registers all possible callbacks (except the process
callback and the timebase callback, which would be just too much noise)
and prints some information whenever they are called.
"""

from threading import Thread

import cv2
import jack

from musejack.players import Video, Audio

print('setting error/info functions')


@jack.set_error_function
def error(msg):
    print('Error:', msg)


@jack.set_info_function
def info(msg):
    print('Info:', msg)


print('starting chatty client')

client = jack.Client('Video-Client')

if client.status.server_started:
    print('JACK server was started')
else:
    print('JACK server was already running')
if client.status.name_not_unique:
    print('unique client name generated:', client.name)

print('registering callbacks')


@client.set_shutdown_callback
def shutdown(status, reason):
    print('JACK shutdown!')
    print('status:', status)
    print('reason:', reason)


@client.set_blocksize_callback
def blocksize(blocksize):
    print('setting blocksize to', blocksize)


@client.set_samplerate_callback
def samplerate(samplerate):
    print('setting samplerate to', samplerate)


@client.set_client_registration_callback
def client_registration(name, register):
    print('client', repr(name), ['unregistered', 'registered'][register])


@client.set_xrun_callback
def xrun(delay):
    print('xrun; delay', delay, 'microseconds')


def realtime(f):
    return f


class Player:

    def __init__(self, filename="the_box.mp4", audio_frame_rate=44100):
        self.filename = filename
        self.audio_frame_rate = audio_frame_rate

        # load video
        self.vcap = cv2.VideoCapture(filename)

        # get fps, total frame count and other important
        self.fps = round(self.vcap.get(cv2.CAP_PROP_FPS))
        self.total_frames_amount = round(self.vcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.audio_frames_per_video_frame = self.audio_frame_rate / self.fps

        # text variable do draw extra stuff on the video
        self.text = None
        self.text_frame = 0  # how long the text has been on the screen
        self.text_frames_max = self.fps * 1.5  # by default, 1.5 seconds

        # other state variables:
        self.new_frame_needed = False
        self.on_frame = 0
        self.previous_frame = 0
        self.seek_requested = -1

        # start the playloop
        Thread(target=self.loop).start()

    @realtime
    def seek(self, frame, is_audio_frame=False):
        if is_audio_frame:
            frame = frame / self.audio_frames_per_video_frame

        self.seek_requested = frame
        self.new_frame_needed = True

    @realtime
    def step(self, audio_frames):
        if self.on_frame * self.audio_frames_per_video_frame < audio_frames:
            self.new_frame_needed = True

    def render(self):
        if self.new_frame_needed:
            self.new_frame_needed = False
            # first check if we have a requested seek
            if self.seek_requested >= 0:
                # check if the seek is higher than the end than the file
                if self.seek_requested >= self.total_frames_amount:
                    self.stop()
                    print("Seek was later than the video, stopping")
                    return
                else:
                    # succesful seek
                    self.vcap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_requested)
                    self.on_frame = self.seek_requested

                    self.text = TextField.normal("Zoo wee mama", self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH))

                self.seek_requested = -1
            else:
                self.on_frame += 1

            # then check if the next frame we want to display is still in the bounds of the video
            if self.on_frame >= self.total_frames_amount:  # technically if a seek happens we are checking this twice in a single call
                self.stop()
                print("End of the video, stopping")
                return

            ret, frame = self.vcap.read()
            if ret:
                # Display the resulting frame
                if self.text:
                    self.text.draw(frame)

                    if self.text.done():
                        self.text = None

                frameS = cv2.resize(frame, (480, 360), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
                cv2.imshow("output", frameS)

                # Press Q on keyboard to  exit
                if cv2.waitKey(1):
                    return

    def loop(self):
        while True:
            self.render()

    def stop(self):
        self.vcap.release()
        cv2.destroyAllWindows()


current_state = -1
player = Video(client, "the_box.mp4")
music = Audio(client, "Orch.wav")


@client.set_timebase_callback
def callback(state: int, blocksize: int, position, new_pos: bool) -> None:
    global current_state
    if state != current_state:
        # if the new state is the rolling state, start the video
        print(f"new state {state}")
        if state == jack.ROLLING:
            print(f"seeking to audio frame {position.frame}")
            player._seek(position.frame)
            music._seek(position.frame)

        current_state = state

    player._step(position.frame)
    music._step(position.frame)


def start_jack():
    print('activating JACK')
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
            print('#' * 80)
            print('press Return to quit')
            print('#' * 80)
            input()
            print('closing JACK')
    except Exception as e:
        print(e)


class TextField:
    """

    """

    def __init__(self, text="Hello World", middle=(200, 200), duration=60):
        self.duration = duration
        self.middle = middle
        self.text = text

        self.font_face = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.4
        self.color = (0, 0, 0)
        self.thickness = cv2.FILLED

        self.drawn_frames = 0

        txt_size = cv2.getTextSize(text, self.font_face, self.scale, self.thickness)

        # from the middle coordinates, get the start and end coordinates
        self.start_x = round(middle[0] + txt_size[0][0] / 2)
        self.start_y = round(middle[1] - txt_size[0][1] / 2)
        self.end_x = middle[0] + txt_size[0][0] / 2
        self.end_y = middle[1] - txt_size[0][1] / 2

    @staticmethod
    def normal(text, frame_width, offset_width=0, offset_height=0):
        # we want the start height to be
        return TextField(text, middle=((frame_width + offset_width) / 2, 200 + offset_height))

    @staticmethod
    def center(text, frame_width, frame_height, offset_width=0, offset_height=0):
        return TextField(text, middle=((frame_width + offset_width) / 2, (frame_height + offset_height) / 2))

    def draw(self, image):
        self.drawn_frames += 1
        cv2.putText(image, self.text, (self.start_x, self.start_y), self.font_face, self.scale, self.color, 1,
                    cv2.LINE_AA)

    def done(self) -> bool:
        if self.drawn_frames > self.duration:
            return True
        return False


start_jack()
