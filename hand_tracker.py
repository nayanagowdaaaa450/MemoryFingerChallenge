import cv2
import os
import urllib.request
import numpy as np
from collections import deque
from statistics import mode
import mediapipe as mp

# Try importing legacy mp.solutions if present
try:
    from mediapipe import solutions as mp_solutions
    HAS_SOLUTIONS = True
except ImportError:
    HAS_SOLUTIONS = False

# 21 Hand landmark bone connections for drawing skeleton
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
]

class HandTracker:
    """
    Universal MediaPipe Hand Tracker compatible with all MediaPipe versions (0.8.x through 0.10.x+).
    Performs landmark extraction, finger counting, and temporal answer stabilization.
    """
    def __init__(self, buffer_size=3):
        self.buffer = deque(maxlen=buffer_size)
        self.finger_tips = [8, 12, 16, 20]
        self.finger_pips = [6, 10, 14, 18]
        self.use_tasks_api = not HAS_SOLUTIONS

        if HAS_SOLUTIONS and hasattr(mp_solutions, 'hands'):
            # Legacy mp.solutions API
            self.mp_hands = mp_solutions.hands
            self.mp_draw = mp_solutions.drawing_utils
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
        else:
            # Modern MediaPipe Tasks API (0.10.x+)
            self.use_tasks_api = True
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
            if not os.path.exists(model_path):
                print("Downloading hand_landmarker.task model file...")
                url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
                urllib.request.urlretrieve(url, model_path)

            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                running_mode=vision.RunningMode.IMAGE
            )
            self.detector = vision.HandLandmarker.create_from_options(options)

    def count_raw_fingers(self, landmarks, handedness="Right"):
        """
        Calculates extended fingers from 21 MediaPipe hand landmarks.
        Returns: (total_count, list_of_finger_states [Thumb, Index, Middle, Ring, Pinky])
        """
        def get_dist(p1, p2):
            z1 = getattr(p1, 'z', 0)
            z2 = getattr(p2, 'z', 0)
            return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (z1 - z2)**2)**0.5

        finger_states = []

        # 1. Robust Distance-Based Thumb Check (Pinky MCP Landmark 17 Reference)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        pinky_mcp = landmarks[17]

        dist_tip_pinky = get_dist(thumb_tip, pinky_mcp)
        dist_ip_pinky = get_dist(thumb_ip, pinky_mcp)

        thumb_open = dist_tip_pinky > dist_ip_pinky
        finger_states.append(1 if thumb_open else 0)

        # 2. Four Fingers (Index 8, Middle 12, Ring 16, Pinky 20)
        # Combines Y-position check and Wrist-distance ratio for rock-solid 2-finger (Index+Middle) detection
        wrist = landmarks[0]
        finger_mcps = [5, 9, 13, 17]

        for tip, pip, mcp in zip(self.finger_tips, self.finger_pips, finger_mcps):
            is_higher = landmarks[tip].y < landmarks[pip].y
            dist_tip_w = get_dist(landmarks[tip], wrist)
            dist_mcp_w = get_dist(landmarks[mcp], wrist)
            is_farther = dist_tip_w > (dist_mcp_w * 1.15)

            if is_higher or is_farther:
                finger_states.append(1)  # Extended
            else:
                finger_states.append(0)  # Folded

        return sum(finger_states), finger_states

    def process_frame(self, frame):
        """
        Processes frame, draws landmarks, and returns:
        (stabilized_count, raw_count, hand_detected, frame, finger_states)
        """
        h, w, c = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_detected = False
        raw_count = 0
        finger_states = [0, 0, 0, 0, 0]

        if not self.use_tasks_api:
            # Legacy mp.solutions path
            results = self.hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                hand_detected = True
                for hand_landmarks, hand_info in zip(results.multi_hand_landmarks, results.multi_handedness):
                    handedness = hand_info.classification[0].label
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                        self.mp_draw.DrawingSpec(color=(255, 100, 0), thickness=2)
                    )
                    raw_count, finger_states = self.count_raw_fingers(hand_landmarks.landmark, handedness)
                    self.buffer.append(raw_count)
        else:
            # Tasks API path
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.detector.detect(mp_image)

            if detection_result.hand_landmarks:
                hand_detected = True
                landmarks = detection_result.hand_landmarks[0]
                
                handedness = "Right"
                if detection_result.handedness:
                    handedness = detection_result.handedness[0][0].category_name

                # Draw skeleton lines and landmark dots
                coords = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
                for p1, p2 in HAND_CONNECTIONS:
                    cv2.line(frame, coords[p1], coords[p2], (255, 100, 0), 2)
                for x, y in coords:
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                raw_count, finger_states = self.count_raw_fingers(landmarks, handedness)
                self.buffer.append(raw_count)

        if not hand_detected:
            self.buffer.append(0)

        stabilized_count = mode(self.buffer) if self.buffer else 0
        return stabilized_count, raw_count, hand_detected, frame, finger_states

    def close(self):
        if not self.use_tasks_api:
            self.hands.close()
        else:
            self.detector.close()
