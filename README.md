# 🖐️ Memory Finger Challenge

**Memory Finger Challenge** is a real-time computer vision memory game built using **Python, OpenCV, and MediaPipe**.

The game tests your short-term visual memory and hand-gesture recognition. The core mechanic is that the relationship between images and numbers (1 to 5) is **randomized at the start of every game**, preventing players from memorizing fixed pairs!

---

## 🎮 Game Concept & Rules

1. **Random Mapping**: 5 images (`Cat`, `Apple`, `Car`, `Tree`, `Ball`) are randomly assigned numbers `1, 2, 3, 4, 5`.
2. **Memorization Phase (8s)**: You get 8 seconds to memorize the temporary mapping.
3. **Question Phase (5s)**: An image is displayed without its number. You must recall its number and raise that many fingers to your webcam!
4. **MediaPipe Gesture Recognition**: The webcam counts your raised fingers in real-time with sub-frame response speed (~30ms latency).
5. **Scoring**: Play through 10 rounds to receive your final score and accuracy percentage.

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **OpenCV (`cv2`)**: Rendering canvas, cards grid, camera feed, and HUD overlays.
- **MediaPipe**: 21 3D hand landmark extraction & joint geometry algorithms.
- **NumPy**: Matrix and image canvas array operations.

---

## 🚀 Quick Start & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/MemoryFingerChallenge.git
cd MemoryFingerChallenge
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the game
```bash
python main.py
```

---

## ⌨️ Controls

- **`SPACE`**: Start Game / Retry after Game Over
- **`R`**: Restart game at any moment with a fresh random mapping
- **`ESC` / `Q`**: Exit game
