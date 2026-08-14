import cv2
import numpy as np
import time
from game_logic import GameManager, GameState
from hand_tracker import HandTracker
from ui_renderer import UIRenderer

def main():
    # Window dimensions
    width, height = 1280, 720

    # Initialize modules
    tracker = HandTracker(buffer_size=3)
    game = GameManager(total_rounds=10, memorization_time=8, answer_time=5, feedback_time=2)
    ui = UIRenderer(images_dir="images", width=width, height=height)

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam device 0.", flush=True)
        return

    # Set camera resolution to 1280x720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    cv2.namedWindow("Memory Finger Challenge", cv2.WINDOW_AUTOSIZE)
    print("Memory Finger Challenge running! Press SPACE to start, ESC to exit.", flush=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Camera frame read failed.", flush=True)
            break

        # Flip frame horizontally for intuitive mirror view
        frame = cv2.flip(frame, 1)

        # Process hand landmarks and count fingers using HandTracker
        stabilized_count, raw_count, hand_detected, processed_frame, _ = tracker.process_frame(frame)

        # Create blank canvas (1280x720, 3 channels)
        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        # -------------------------------------------------------------
        # GAME STATE MACHINE
        # -------------------------------------------------------------
        if game.state == GameState.START:
            ui.draw_start_screen(canvas)

        elif game.state == GameState.MEMORIZE:
            time_left = game.get_memorization_time_remaining()
            ui.draw_memorization_screen(canvas, game.mapping, time_left)

            # Move to Question phase when memorization timer hits 0
            if time_left <= 0:
                game.next_question()

        elif game.state == GameState.QUESTION:
            time_left = game.get_answer_time_remaining()
            ui.draw_question_screen(
                canvas, processed_frame, game.current_question_image,
                game.current_round, game.total_rounds, game.score,
                time_left, stabilized_count, hand_detected
            )

            # Submit answer when timer hits 0
            if time_left <= 0:
                game.submit_answer(stabilized_count)

        elif game.state == GameState.FEEDBACK:
            time_left = game.get_feedback_time_remaining()
            ui.draw_feedback_screen(
                canvas, game.is_last_answer_correct, game.correct_answer,
                game.last_detected_answer, game.current_round,
                game.total_rounds, game.score
            )

            # Move to next question or game over when feedback timer finishes
            if time_left <= 0:
                game.next_question()

        elif game.state == GameState.GAME_OVER:
            ui.draw_game_over_screen(canvas, game.score, game.total_rounds, game.get_accuracy())

        # Display full rendered canvas
        cv2.imshow("Memory Finger Challenge", canvas)

        # Keyboard Event Controls
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'): # ESC or q to exit
            break
        elif key == 32: # SPACE to start or play again
            if game.state in [GameState.START, GameState.GAME_OVER]:
                game.start_new_game()
        elif key == ord('r') or key == ord('R'): # R to restart game at any point
            game.start_new_game()

    # Clean shutdown
    tracker.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Game closed cleanly. Thanks for playing!", flush=True)

if __name__ == "__main__":
    main()
