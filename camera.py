import copy
import time
import threading
from _thread import get_ident

import cv2


__all__ = [
    "Camera",
    "stream_generator",
    "from_webcam"
]


DELAY_REMOVE = 1


class CameraEvent(object):
    """ An Event-like class that signals all active clients when 
        a new frame is available. """

    events_total = 0

    def __init__(self):
        self.events = {}

    def wait(self):
        """ Invoked from each client's thread to wait for the next frame. """
        ident = get_ident()
        if ident not in self.events:
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """ Invoked by the camera thread when a new frame is available. """
        now = time.time()
        remove = []
        for ident, event in self.events.items():
            if not event[0].isSet():
                event[0].set()
                event[1] = now
            else:
                if now - event[1] > DELAY_REMOVE:
                    remove.append(ident)

        for ident in remove:        
            del self.events[ident]
        self.events_total = len(self.events)

    def clear(self):
        """ Invoked from each client's thread after a frame was processed. """
        self.events[get_ident()][0].clear()


class Camera():

    thread = None

    frame = None

    last_access = 0

    event = CameraEvent()

    def __new__(cls, source):
        cls.source = source
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        """ Start the background camera thread if it isn't running yet. """
        if Camera.thread is None:
            Camera.last_access = time.time()

            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """ Return the current camera frame. """
        Camera.last_access = time.time()

        Camera.event.wait()
        Camera.event.clear()

        return Camera.frame

    @classmethod
    def _thread(cls):
        frames_iterator = cls.source()
        for frame in frames_iterator:
            Camera.frame = frame
            Camera.event.set()
            time.sleep(0)

            if time.time() - Camera.last_access > 10:
                frames_iterator.close()
                break
        Camera.thread = None


def stream_generator(camera):
    while True:
        frame = camera.get_frame()
        # Preprocess frame
        frame = cv2.putText(
            frame, f"WATCHING:{Camera.event.events_total}",
            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
            .7, (255, 255, 255), 1, cv2.LINE_AA
        )
        image = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (
            b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image + b'\r\n'
        )


def from_webcam():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError('Could not start camera.')

    while True:
        _, img = camera.read()
        yield img


def from_file():
    ...
