import os
import random
import time

class GameState:
    START = "START"
    MEMORIZE = "MEMORIZE"
    QUESTION = "QUESTION"
    FEEDBACK = "FEEDBACK"
    GAME_OVER = "GAME_OVER"

class GameManager:
    """
    Handles core game logic:
    - Random mapping generation (1 to 5) for 5 images at game start
    - Round management (10 rounds max)
    - Prevention of immediate consecutive image repeats
    - Timer management for Memorization, Question, and Feedback phases
    - Score and accuracy tracking
    """
    def __init__(self, images_dir="images", total_rounds=10, memorization_time=8, answer_time=5, feedback_time=2):
        if not os.path.isabs(images_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(base_dir, images_dir)
        self.images_dir = images_dir
        self.total_rounds = total_rounds
        self.memorization_time = memorization_time
        self.answer_time = answer_time
        self.feedback_time = feedback_time

        self.image_names = ["cat.jpg", "apple.jpg", "car.jpg", "tree.jpg", "ball.jpg"]
        self.state = GameState.START
        
        self.mapping = {}
        self.score = 0
        self.current_round = 0
        self.current_question_image = None
        self.correct_answer = 0
        self.last_detected_answer = 0
        self.is_last_answer_correct = False
        
        self.phase_start_time = 0
        self.last_question_image = None

    def start_new_game(self):
        """
        Randomly assigns numbers 1, 2, 3, 4, 5 to the 5 images for the new game.
        """
        numbers = [1, 2, 3, 4, 5]
        random.shuffle(numbers)
        self.mapping = {img: num for img, num in zip(self.image_names, numbers)}
        
        self.score = 0
        self.current_round = 0
        self.last_question_image = None
        self.state = GameState.MEMORIZE
        self.phase_start_time = time.time()

    def get_memorization_time_remaining(self):
        elapsed = time.time() - self.phase_start_time
        return max(0, int(self.memorization_time - elapsed))

    def get_answer_time_remaining(self):
        elapsed = time.time() - self.phase_start_time
        return max(0, int(self.answer_time - elapsed))

    def get_feedback_time_remaining(self):
        elapsed = time.time() - self.phase_start_time
        return max(0, int(self.feedback_time - elapsed))

    def next_question(self):
        self.current_round += 1
        if self.current_round > self.total_rounds:
            self.state = GameState.GAME_OVER
            return

        # Select random image, avoiding consecutive repeat
        available_images = [img for img in self.image_names if img != self.last_question_image]
        if not available_images:
            available_images = self.image_names
            
        self.current_question_image = random.choice(available_images)
        self.last_question_image = self.current_question_image
        self.correct_answer = self.mapping[self.current_question_image]
        
        self.state = GameState.QUESTION
        self.phase_start_time = time.time()

    def submit_answer(self, detected_fingers):
        self.last_detected_answer = detected_fingers
        if detected_fingers == self.correct_answer:
            self.score += 1
            self.is_last_answer_correct = True
        else:
            self.is_last_answer_correct = False
            
        self.state = GameState.FEEDBACK
        self.phase_start_time = time.time()

    def get_accuracy(self):
        if self.total_rounds == 0:
            return 0.0
        return round((self.score / self.total_rounds) * 100, 1)
