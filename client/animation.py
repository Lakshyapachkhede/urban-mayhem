class Animation:
    def __init__(self, frames, frame_time=0.10, current_frame=0, loop=True):
        self.frames_count = len(frames)
        self.frames = frames
        self.frame_time = frame_time
        self.loop = loop
        self.current_frame = current_frame
        self.timer = 0

    def update(self, dt):
        self.timer += dt

        while (self.timer >= self.frame_time):
            self.timer -= self.frame_time
            self.current_frame += 1

            if (self.current_frame >= self.frames_count):
                self.current_frame = 0 if (self.loop) else self.frames_count - 1

    def get_current_frame(self):
        return self.frames[self.current_frame]
        
    
