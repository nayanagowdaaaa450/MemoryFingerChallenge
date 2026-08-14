import cv2
import os
import numpy as np

class UIRenderer:
    """
    Handles all UI rendering, card layouts, timers, HUDs, feedback banners,
    and image overlays using OpenCV functions.
    """
    def __init__(self, images_dir="images", width=1280, height=720):
        self.width = width
        self.height = height
        if not os.path.isabs(images_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(base_dir, images_dir)
        self.images_dir = images_dir
        self.loaded_images = {}
        self.load_all_images()

    def load_all_images(self):
        """Loads and pre-resizes images for cards and questions."""
        filenames = ["cat.jpg", "apple.jpg", "car.jpg", "tree.jpg", "ball.jpg"]
        for fname in filenames:
            path = os.path.join(self.images_dir, fname)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    self.loaded_images[fname] = img
                else:
                    print(f"Warning: Failed to decode image {fname}")
            else:
                print(f"Warning: Image file missing: {path}")

    def draw_header(self, canvas, title, round_num=None, total_rounds=10, score=None, timer_sec=None):
        """Renders header banner with game title, round, score, and countdown timer."""
        cv2.rectangle(canvas, (0, 0), (self.width, 70), (25, 25, 35), -1)
        cv2.line(canvas, (0, 70), (self.width, 70), (0, 255, 255), 2)

        # Title
        cv2.putText(canvas, title, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Round & Score
        if round_num is not None and score is not None:
            round_text = f"Round: {round_num}/{total_rounds}"
            score_text = f"Score: {score}"
            cv2.putText(canvas, round_text, (self.width - 450, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(canvas, score_text, (self.width - 250, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Timer Badge
        if timer_sec is not None:
            timer_text = f"Time: {timer_sec}s"
            color = (0, 0, 255) if timer_sec <= 3 else (0, 255, 255)
            cv2.putText(canvas, timer_text, (self.width - 110, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    def draw_start_screen(self, canvas):
        """Renders Start Screen layout."""
        canvas[:] = (30, 25, 20)  # Dark sleek background

        # Header Title Box
        cv2.rectangle(canvas, (100, 80), (self.width - 100, 200), (45, 40, 35), -1)
        cv2.rectangle(canvas, (100, 80), (self.width - 100, 200), (0, 255, 255), 3)
        
        cv2.putText(canvas, "MEMORY FINGER CHALLENGE", (self.width // 2 - 320, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        cv2.putText(canvas, "Computer Vision Memory & Hand Gesture Game", (self.width // 2 - 270, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

        # Instructions Box
        cv2.rectangle(canvas, (150, 240), (self.width - 150, 560), (35, 30, 25), -1)
        cv2.rectangle(canvas, (150, 240), (self.width - 150, 560), (100, 100, 100), 1)

        instructions = [
            "HOW TO PLAY:",
            "1. 5 images will be assigned random numbers (1 to 5) at game start.",
            "2. You have 8 seconds to MEMORIZE the random image-to-number mapping.",
            "3. During Question rounds, an image is displayed without its number.",
            "4. Show that number of fingers (1 to 5) to your webcam to answer!",
            "5. Complete 10 rounds to test your score and accuracy."
        ]

        y_offset = 290
        for idx, text in enumerate(instructions):
            color = (0, 255, 255) if idx == 0 else (240, 240, 240)
            scale = 0.8 if idx == 0 else 0.65
            thick = 2 if idx == 0 else 1
            cv2.putText(canvas, text, (180, y_offset), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick)
            y_offset += 42

        # Start Prompt Button
        cv2.rectangle(canvas, (self.width // 2 - 220, 590), (self.width // 2 + 220, 660), (0, 200, 0), -1)
        cv2.putText(canvas, "Press SPACE to Start Game", (self.width // 2 - 180, 635),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    def draw_memorization_screen(self, canvas, mapping, time_left):
        """Renders 5 image cards with their randomly assigned numbers (1 to 5)."""
        canvas[:] = (30, 25, 20)
        self.draw_header(canvas, "MEMORIZATION PHASE - Memorize the Mapping!", timer_sec=time_left)

        # Card layout: 3 cards top row, 2 cards bottom row
        card_w, card_h = 210, 240
        top_positions = [(130, 120), (535, 120), (940, 120)]
        bottom_positions = [(330, 410), (740, 410)]
        all_positions = top_positions + bottom_positions

        filenames = ["cat.jpg", "apple.jpg", "car.jpg", "tree.jpg", "ball.jpg"]
        labels = ["CAT", "APPLE", "CAR", "TREE", "BALL"]

        for idx, (fname, label) in enumerate(zip(filenames, labels)):
            x, y = all_positions[idx]
            assigned_num = mapping.get(fname, "?")

            # Card Container
            cv2.rectangle(canvas, (x, y), (x + card_w, y + card_h), (45, 40, 35), -1)
            cv2.rectangle(canvas, (x, y), (x + card_w, y + card_h), (0, 255, 255), 2)

            # Draw Thumbnail Image
            if fname in self.loaded_images:
                thumb = cv2.resize(self.loaded_images[fname], (150, 130))
                canvas[y + 15:y + 145, x + 30:x + 180] = thumb

            # Image Label
            cv2.putText(canvas, label, (x + 20, y + 170), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            # Number Badge Circle
            cv2.circle(canvas, (x + card_w - 40, y + card_h - 40), 30, (0, 255, 255), -1)
            cv2.putText(canvas, str(assigned_num), (x + card_w - 52, y + card_h - 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)

        # Bottom Warning
        cv2.putText(canvas, "Numbers will HIDE when timer reaches 0!", (self.width // 2 - 250, 690),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    def draw_question_screen(self, canvas, webcam_frame, question_image, round_num, total_rounds, score, time_left, detected_fingers, hand_detected):
        """Renders Question prompt on left side and live hand webcam tracking feed on right side."""
        canvas[:] = (30, 25, 20)
        self.draw_header(canvas, "QUESTION PHASE - Show correct fingers!", round_num, total_rounds, score, time_left)

        # Left Column: Question Card (Width: 480)
        cv2.rectangle(canvas, (30, 90), (510, 680), (45, 40, 35), -1)
        cv2.rectangle(canvas, (30, 90), (510, 680), (0, 255, 255), 2)

        cv2.putText(canvas, "WHAT WAS THE NUMBER FOR:", (60, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

        # Question Image Thumbnail
        if question_image in self.loaded_images:
            q_img = cv2.resize(self.loaded_images[question_image], (320, 300))
            canvas[160:460, 110:430] = q_img

        # Image Label (NO NUMBER DISPLAYED!)
        clean_name = question_image.replace(".jpg", "").upper()
        cv2.putText(canvas, clean_name, (200, 495), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)

        cv2.putText(canvas, "Show fingers to camera!", (130, 545),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Live Answer Box
        hand_status = f"Detected: {detected_fingers} finger(s)" if hand_detected else "No Hand Detected"
        status_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        cv2.rectangle(canvas, (50, 580), (490, 650), (20, 20, 20), -1)
        cv2.rectangle(canvas, (50, 580), (490, 650), status_color, 2)
        cv2.putText(canvas, hand_status, (70, 625), cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2)

        # Right Column: Live Camera Feed (Resized to 700x570)
        if webcam_frame is not None:
            cam_resized = cv2.resize(webcam_frame, (700, 590))
            canvas[90:680, 540:1240] = cam_resized
            cv2.rectangle(canvas, (540, 90), (1240, 680), (0, 255, 255), 2)

    def draw_feedback_screen(self, canvas, is_correct, correct_num, detected_num, round_num, total_rounds, score):
        """Renders Correct or Wrong feedback banner overlay."""
        self.draw_header(canvas, "ROUND RESULT", round_num, total_rounds, score)

        banner_y1, banner_y2 = 220, 500
        if is_correct:
            # Green Banner
            cv2.rectangle(canvas, (150, banner_y1), (self.width - 150, banner_y2), (20, 100, 20), -1)
            cv2.rectangle(canvas, (150, banner_y1), (self.width - 150, banner_y2), (0, 255, 0), 4)
            cv2.putText(canvas, "CORRECT!", (self.width // 2 - 140, 310),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 0), 4)
            cv2.putText(canvas, "+1 POINT!", (self.width // 2 - 90, 380),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(canvas, f"You showed {detected_num} finger(s)", (self.width // 2 - 160, 440),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 200), 2)
        else:
            # Red Banner
            cv2.rectangle(canvas, (150, banner_y1), (self.width - 150, banner_y2), (20, 20, 100), -1)
            cv2.rectangle(canvas, (150, banner_y1), (self.width - 150, banner_y2), (0, 0, 255), 4)
            cv2.putText(canvas, "WRONG!", (self.width // 2 - 120, 310),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 255), 4)
            cv2.putText(canvas, f"Correct Answer was: {correct_num}", (self.width // 2 - 190, 380),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
            cv2.putText(canvas, f"You showed: {detected_num} finger(s)", (self.width // 2 - 150, 440),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 255), 2)

    def draw_game_over_screen(self, canvas, score, total_rounds, accuracy):
        """Renders Game Over final summary card."""
        canvas[:] = (30, 25, 20)

        # Main Card Box
        cv2.rectangle(canvas, (200, 100), (self.width - 200, 620), (45, 40, 35), -1)
        cv2.rectangle(canvas, (200, 100), (self.width - 200, 620), (0, 255, 255), 3)

        cv2.putText(canvas, "GAME OVER!", (self.width // 2 - 160, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)

        # Score Box
        cv2.rectangle(canvas, (300, 230), (self.width - 300, 480), (25, 20, 15), -1)
        cv2.rectangle(canvas, (300, 230), (self.width - 300, 480), (100, 100, 100), 1)

        cv2.putText(canvas, f"Final Score:  {score} / {total_rounds}", (self.width // 2 - 180, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
        cv2.putText(canvas, f"Accuracy:     {accuracy}%", (self.width // 2 - 180, 370),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)

        # Grade Evaluation
        grade = "EXCELLENT MEMORY! 🏆" if accuracy >= 80 else ("GOOD JOB! 👍" if accuracy >= 50 else "KEEP PRACTICING! 🧠")
        cv2.putText(canvas, grade, (self.width // 2 - 170, 440),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        # Restart Instructions
        cv2.rectangle(canvas, (self.width // 2 - 250, 520), (self.width // 2 + 250, 590), (0, 200, 0), -1)
        cv2.putText(canvas, "Press SPACE or 'R' to Play Again", (self.width // 2 - 230, 565),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
