"""
direction_mapper.py — Angle to Directional State Classifier
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)

Maps continuous head pose angles (pitch, yaw) and eye gaze angles (pitch, yaw)
to discrete directional states: LEFT, RIGHT, UP, DOWN, CENTER.
"""

import math

class DirectionMapper:
    """
    Configurable Angle-to-Direction Classifier for Head Pose and Eye Gaze.
    All internal angles are processed in radians (or degrees).
    """
    def __init__(self,
                 head_yaw_left=-0.18,    # ~ -10 degrees
                 head_yaw_right=0.18,    # ~ +10 degrees
                 head_pitch_up=-0.15,   # ~ -8.5 degrees
                 head_pitch_down=0.15,  # ~ +8.5 degrees
                 gaze_yaw_left=-0.22,    # ~ -12.5 degrees
                 gaze_yaw_right=0.22,    # ~ +12.5 degrees
                 gaze_pitch_up=-0.18,   # ~ -10 degrees
                 gaze_pitch_down=0.18): # ~ +10 degrees
        
        self.head_yaw_left = head_yaw_left
        self.head_yaw_right = head_yaw_right
        self.head_pitch_up = head_pitch_up
        self.head_pitch_down = head_pitch_down

        self.gaze_yaw_left = gaze_yaw_left
        self.gaze_yaw_right = gaze_yaw_right
        self.gaze_pitch_up = gaze_pitch_up
        self.gaze_pitch_down = gaze_pitch_down

    def map_head_direction(self, pitch, yaw):
        """
        Maps head pitch and yaw to direction state.
        :param pitch: float (radians or converted degrees)
        :param yaw: float (radians or converted degrees)
        :return: str ("LEFT", "RIGHT", "UP", "DOWN", "CENTER")
        """
        # Yaw takes precedence for left/right
        if yaw < self.head_yaw_left:
            return "LEFT"
        elif yaw > self.head_yaw_right:
            return "RIGHT"

        # Pitch for up/down
        if pitch < self.head_pitch_up:
            return "UP"
        elif pitch > self.head_pitch_down:
            return "DOWN"

        return "CENTER"

    def map_gaze_direction(self, pitch, yaw):
        """
        Maps eye gaze pitch and yaw to direction state.
        :param pitch: float (radians or converted degrees)
        :param yaw: float (radians or converted degrees)
        :return: str ("LEFT", "RIGHT", "UP", "DOWN", "CENTER")
        """
        if yaw < self.gaze_yaw_left:
            return "LEFT"
        elif yaw > self.gaze_yaw_right:
            return "RIGHT"

        if pitch < self.gaze_pitch_up:
            return "UP"
        elif pitch > self.gaze_pitch_down:
            return "DOWN"

        return "CENTER"

    def process(self, head_pitch, head_yaw, gaze_pitch, gaze_yaw):
        """
        Processes head and gaze pitch/yaw angles and returns comprehensive dictionary.
        """
        head_dir = self.map_head_direction(head_pitch, head_yaw)
        gaze_dir = self.map_gaze_direction(gaze_pitch, gaze_yaw)

        return {
            "head": {
                "direction": head_dir,
                "pitch_rad": round(float(head_pitch), 4),
                "yaw_rad": round(float(head_yaw), 4),
                "pitch_deg": round(math.degrees(head_pitch), 2),
                "yaw_deg": round(math.degrees(head_yaw), 2)
            },
            "gaze": {
                "direction": gaze_dir,
                "pitch_rad": round(float(gaze_pitch), 4),
                "yaw_rad": round(float(gaze_yaw), 4),
                "pitch_deg": round(math.degrees(gaze_pitch), 2),
                "yaw_deg": round(math.degrees(gaze_yaw), 2)
            }
        }
