// Memory Finger Challenge - Web JS Edition

const IMAGES = [
    { name: "CAT", file: "images/cat.jpg" },
    { name: "APPLE", file: "images/apple.jpg" },
    { name: "CAR", file: "images/car.jpg" },
    { name: "TREE", file: "images/tree.jpg" },
    { name: "BALL", file: "images/ball.jpg" }
];

const GameState = {
    START: "START",
    MEMORIZE: "MEMORIZE",
    QUESTION: "QUESTION",
    FEEDBACK: "FEEDBACK",
    GAME_OVER: "GAME_OVER"
};

class GameApp {
    constructor() {
        this.totalRounds = 10;
        this.memorizeTime = 8;
        this.answerTime = 5;
        this.feedbackTime = 2;

        this.state = GameState.START;
        this.mapping = {};
        this.score = 0;
        this.currentRound = 0;
        this.currentQuestionImage = null;
        this.lastQuestionImage = null;
        this.correctAnswer = 0;

        // Temporal Finger Buffer (3 frames)
        this.fingerBuffer = [];
        this.maxBufferLen = 3;
        this.stabilizedFingers = 0;
        this.handDetected = false;

        this.timerInterval = null;
        this.timeLeft = 0;

        this.initDOM();
        this.initMediaPipe();
        this.bindEvents();
    }

    initDOM() {
        this.screens = {
            start: document.getElementById('screen-start'),
            memorize: document.getElementById('screen-memorize'),
            question: document.getElementById('screen-question'),
            gameOver: document.getElementById('screen-game-over')
        };

        this.hud = {
            round: document.getElementById('hud-round'),
            score: document.getElementById('hud-score'),
            timer: document.getElementById('hud-timer'),
            timerContainer: document.getElementById('hud-timer-container')
        };

        this.memorizeGrid = document.getElementById('cards-grid');
        this.memorizeProgress = document.getElementById('memorize-progress');

        this.questionImg = document.getElementById('question-img');
        this.questionImgLabel = document.getElementById('question-img-label');
        this.liveStatusBox = document.getElementById('live-status-box');
        this.liveGestureText = document.getElementById('live-gesture-text');

        this.feedbackOverlay = document.getElementById('feedback-overlay');
        this.feedbackCard = document.getElementById('feedback-card');
        this.feedbackIcon = document.getElementById('feedback-icon');
        this.feedbackTitle = document.getElementById('feedback-title');
        this.feedbackSubtitle = document.getElementById('feedback-subtitle');
        this.feedbackDetails = document.getElementById('feedback-details');

        this.finalScore = document.getElementById('final-score');
        this.finalAccuracy = document.getElementById('final-accuracy');
        this.gradeBanner = document.getElementById('grade-banner');

        this.btnQuit = document.getElementById('btn-quit');

        this.videoElement = document.getElementById('webcam-video');
        this.canvasElement = document.getElementById('skeleton-canvas');
        this.canvasCtx = this.canvasElement.getContext('2d');
    }

    async initMediaPipe() {
        this.hands = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        this.hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.7
        });

        this.hands.onResults((results) => this.onHandResults(results));

        this.camera = new Camera(this.videoElement, {
            onFrame: async () => {
                await this.hands.send({ image: this.videoElement });
            },
            width: 1280,
            height: 720
        });

        try {
            await this.camera.start();
            console.log("MediaPipe Camera initialized successfully!");
        } catch (err) {
            console.error("Camera access failed:", err);
            this.liveGestureText.innerText = "Error: Camera access denied!";
        }
    }

    bindEvents() {
        document.getElementById('btn-start').addEventListener('click', () => this.startGame());
        document.getElementById('btn-restart').addEventListener('click', () => this.startGame());
        this.btnQuit.addEventListener('click', () => this.quitGame());

        window.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (this.state === GameState.START || this.state === GameState.GAME_OVER) {
                    this.startGame();
                }
            } else if (e.code === 'KeyR') {
                this.startGame();
            } else if (e.code === 'Escape' || e.code === 'KeyQ') {
                this.quitGame();
            }
        });
    }

    quitGame() {
        this.clearInterval();
        this.state = GameState.START;
        this.feedbackOverlay.classList.add('hidden');
        this.btnQuit.classList.add('hidden');
        this.hud.timer.innerText = "8s";
        this.switchScreen('start');
    }

    switchScreen(screenKey) {
        Object.keys(this.screens).forEach(key => {
            this.screens[key].classList.remove('active');
        });
        if (this.screens[screenKey]) {
            this.screens[screenKey].classList.add('active');
        }

        if (screenKey === 'start') {
            this.btnQuit.classList.add('hidden');
        } else {
            this.btnQuit.classList.remove('hidden');
        }
    }

    startGame() {
        // Randomly shuffle [1, 2, 3, 4, 5]
        const numbers = [1, 2, 3, 4, 5].sort(() => Math.random() - 0.5);
        this.mapping = {};
        IMAGES.forEach((img, idx) => {
            this.mapping[img.file] = numbers[idx];
        });

        this.score = 0;
        this.currentRound = 0;
        this.lastQuestionImage = null;
        this.hud.score.innerText = "0";

        this.startMemorizationPhase();
    }

    startMemorizationPhase() {
        this.state = GameState.MEMORIZE;
        this.switchScreen('memorize');

        // Render card grid
        this.memorizeGrid.innerHTML = '';
        IMAGES.forEach(img => {
            const num = this.mapping[img.file];
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <img src="${img.file}" alt="${img.name}">
                <div class="item-name">${img.name}</div>
                <div class="number-badge">${num}</div>
            `;
            this.memorizeGrid.appendChild(card);
        });

        this.startTimer(this.memorizeTime, (time) => {
            this.hud.timer.innerText = `${time}s`;
            const pct = (time / this.memorizeTime) * 100;
            this.memorizeProgress.style.width = `${pct}%`;
        }, () => {
            this.nextQuestion();
        });
    }

    nextQuestion() {
        this.currentRound++;
        if (this.currentRound > this.totalRounds) {
            this.showGameOver();
            return;
        }

        this.hud.round.innerText = `${this.currentRound} / ${this.totalRounds}`;

        // Select random image, avoiding consecutive repeat
        const available = IMAGES.filter(img => img.file !== this.lastQuestionImage);
        const selected = available[Math.floor(Math.random() * available.length)];
        
        this.currentQuestionImage = selected;
        this.lastQuestionImage = selected.file;
        this.correctAnswer = this.mapping[selected.file];

        this.state = GameState.QUESTION;
        this.switchScreen('question');

        this.questionImg.src = selected.file;
        this.questionImgLabel.innerText = selected.name;

        this.startTimer(this.answerTime, (time) => {
            this.hud.timer.innerText = `${time}s`;
        }, () => {
            this.submitAnswer(this.stabilizedFingers);
        });
    }

    submitAnswer(detectedCount) {
        this.clearInterval();
        this.state = GameState.FEEDBACK;

        const isCorrect = (detectedCount === this.correctAnswer);
        if (isCorrect) {
            this.score++;
            this.hud.score.innerText = this.score;
        }

        this.showFeedback(isCorrect, detectedCount);

        setTimeout(() => {
            this.feedbackOverlay.classList.add('hidden');
            this.nextQuestion();
        }, this.feedbackTime * 1000);
    }

    showFeedback(isCorrect, detectedCount) {
        this.feedbackCard.className = 'glass-card feedback-card ' + (isCorrect ? 'feedback-correct' : 'feedback-wrong');
        this.feedbackIcon.innerText = isCorrect ? '✅' : '❌';
        this.feedbackTitle.innerText = isCorrect ? 'CORRECT!' : 'WRONG!';
        this.feedbackSubtitle.innerText = isCorrect ? '+1 POINT' : `Correct Answer was: ${this.correctAnswer}`;
        this.feedbackDetails.innerText = `You showed ${detectedCount} finger(s)`;
        this.feedbackOverlay.classList.remove('hidden');
    }

    showGameOver() {
        this.state = GameState.GAME_OVER;
        this.switchScreen('gameOver');
        this.hud.timer.innerText = "0s";

        const accuracy = ((this.score / this.totalRounds) * 100).toFixed(1);
        this.finalScore.innerText = `${this.score} / ${this.totalRounds}`;
        this.finalAccuracy.innerText = `${accuracy}%`;

        let grade = "EXCELLENT MEMORY! 🏆";
        if (accuracy < 50) grade = "KEEP PRACTICING! 🧠";
        else if (accuracy < 80) grade = "GOOD JOB! 👍";
        this.gradeBanner.innerText = grade;
    }

    startTimer(seconds, onTick, onComplete) {
        this.clearInterval();
        this.timeLeft = seconds;
        onTick(this.timeLeft);

        this.timerInterval = setInterval(() => {
            this.timeLeft--;
            onTick(this.timeLeft);
            if (this.timeLeft <= 0) {
                this.clearInterval();
                onComplete();
            }
        }, 1000);
    }

    clearInterval() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    onHandResults(results) {
        // Resize canvas to match video
        this.canvasElement.width = this.videoElement.videoWidth || 640;
        this.canvasElement.height = this.videoElement.videoHeight || 480;

        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            this.handDetected = true;
            const landmarks = results.multiHandLandmarks[0];

            // Draw skeleton & dots
            drawConnectors(this.canvasCtx, landmarks, HAND_CONNECTIONS, { color: '#00f2fe', lineWidth: 3 });
            drawLandmarks(this.canvasCtx, landmarks, { color: '#00ff87', lineWidth: 2, radius: 4 });

            // Count raw fingers
            const rawCount = this.countFingers(landmarks);
            this.fingerBuffer.push(rawCount);
            if (this.fingerBuffer.length > this.maxBufferLen) {
                this.fingerBuffer.shift();
            }

            // Statistical Mode
            this.stabilizedFingers = this.getMode(this.fingerBuffer);

            if (this.state === GameState.QUESTION) {
                this.liveStatusBox.style.borderColor = '#00ff87';
                this.liveGestureText.innerHTML = `Detected: <strong style="color: #00f2fe">${this.stabilizedFingers}</strong> finger(s)`;
            }
        } else {
            this.handDetected = false;
            this.fingerBuffer.push(0);
            if (this.fingerBuffer.length > this.maxBufferLen) {
                this.fingerBuffer.shift();
            }
            this.stabilizedFingers = this.getMode(this.fingerBuffer);

            if (this.state === GameState.QUESTION) {
                this.liveStatusBox.style.borderColor = '#ff3366';
                this.liveGestureText.innerText = "No Hand Detected - Show hand to camera";
            }
        }

        this.canvasCtx.restore();
    }

    countFingers(landmarks) {
        const getDist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y, (p1.z || 0) - (p2.z || 0));

        let count = 0;

        // 1. Thumb Check (Pinky MCP Landmark 17 Reference)
        const thumbTip = landmarks[4];
        const thumbIp = landmarks[3];
        const pinkyMcp = landmarks[17];

        const distTipPinky = getDist(thumbTip, pinkyMcp);
        const distIpPinky = getDist(thumbIp, pinkyMcp);
        if (distTipPinky > distIpPinky) count++;

        // 2. Four Fingers (Index 8, Middle 12, Ring 16, Pinky 20)
        const wrist = landmarks[0];
        const tips = [8, 12, 16, 20];
        const pips = [6, 10, 14, 18];
        const mcps = [5, 9, 13, 17];

        for (let i = 0; i < 4; i++) {
            const tip = landmarks[tips[i]];
            const pip = landmarks[pips[i]];
            const mcp = landmarks[mcps[i]];

            const isHigher = tip.y < pip.y;
            const distTipW = getDist(tip, wrist);
            const distMcpW = getDist(mcp, wrist);
            const isFarther = distTipW > (distMcpW * 1.15);

            if (isHigher || isFarther) {
                count++;
            }
        }

        return count;
    }

    getMode(arr) {
        if (!arr.length) return 0;
        const counts = {};
        let maxCount = 0;
        let mode = arr[0];

        arr.forEach(val => {
            counts[val] = (counts[val] || 0) + 1;
            if (counts[val] > maxCount) {
                maxCount = counts[val];
                mode = val;
            }
        });
        return mode;
    }
}

// Initialize Web Application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.gameApp = new GameApp();
});
