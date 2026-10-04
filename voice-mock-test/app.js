const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;

const isIOS =
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
const isMobile = isIOS || /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

const state = {
  topic: "java-collection-framework",
  questions: [],
  index: 0,
  score: 0,
  mode: "chat", // chat | voice
  phase: "idle",
  recognition: null,
  listening: false,
  quizRunning: false,
  waitingForNext: false,
};

const els = {
  topicTitle: document.getElementById("topicTitle"),
  topicLevel: document.getElementById("topicLevel"),
  questionNum: document.getElementById("questionNum"),
  questionText: document.getElementById("questionText"),
  transcript: document.getElementById("transcript"),
  feedback: document.getElementById("feedback"),
  score: document.getElementById("score"),
  status: document.getElementById("status"),
  micIndicator: document.getElementById("micIndicator"),
  startBtn: document.getElementById("startBtn"),
  repeatBtn: document.getElementById("repeatBtn"),
  skipBtn: document.getElementById("skipBtn"),
  stopBtn: document.getElementById("stopBtn"),
  log: document.getElementById("log"),
  chatModeBtn: document.getElementById("chatModeBtn"),
  voiceModeBtn: document.getElementById("voiceModeBtn"),
  answerInput: document.getElementById("answerInput"),
  submitAnswerBtn: document.getElementById("submitAnswerBtn"),
  answerInputRow: document.getElementById("answerInputRow"),
  modeHint: document.getElementById("modeHint"),
};

function log(message, type = "info") {
  const entry = document.createElement("div");
  entry.className = `log-entry log-${type}`;
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  els.log.prepend(entry);
}

function setStatus(text, active = false) {
  els.status.textContent = text;
  els.micIndicator.classList.toggle("active", active);
}

function normalize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function speak(text) {
  return new Promise((resolve) => {
    if (!synth || state.mode !== "voice") {
      resolve();
      return;
    }
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = isIOS ? 0.9 : 0.95;
    utterance.lang = "en-US";
    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();
    synth.speak(utterance);
  });
}

function extractMcqChoice(text) {
  const n = normalize(text);
  const patterns = [
    /\b(option\s*)?([abcd])\b/,
    /\b([abcd])\s+is\b/,
    /\banswer\s+is\s+([abcd])\b/,
    /\b([abcd])\b/,
  ];
  for (const pattern of patterns) {
    const match = n.match(pattern);
    if (match) return match[match.length - 1].toUpperCase();
  }

  const optionNames = {
    arraylist: "A",
    linkedlist: "B",
    hashset: "C",
    treeset: "D",
    hashmap: "A",
    treemap: "B",
    linkedhashmap: "C",
    hashtable: "D",
    concurrenthashmap: "B",
  };
  for (const [name, letter] of Object.entries(optionNames)) {
    if (n.includes(name)) return letter;
  }
  return null;
}

function gradeAnswer(question, rawAnswer) {
  const answer = normalize(rawAnswer);
  if (!answer) {
    return { verdict: "Incorrect", correct: false, partial: false };
  }

  if (question.type === "mcq") {
    const choice = extractMcqChoice(rawAnswer);
    const correct = choice === question.correct;
    return { verdict: correct ? "Correct" : "Incorrect", correct, partial: false, choice };
  }

  const groups = question.keywords || [];
  const minGroups = question.minKeywordGroups || 1;
  let matchedGroups = 0;

  for (const group of groups) {
    if (group.some((keyword) => answer.includes(normalize(keyword)))) {
      matchedGroups += 1;
    }
  }

  if (matchedGroups >= minGroups) {
    return { verdict: "Correct", correct: true, partial: false };
  }
  if (matchedGroups > 0) {
    return { verdict: "Partially correct", correct: false, partial: true };
  }
  return { verdict: "Incorrect", correct: false, partial: false };
}

function buildFeedback(question, result) {
  let text = `Verdict: ${result.verdict}. `;
  if (result.correct) {
    text += "Well done. ";
    state.score += 1;
  } else if (result.partial) {
    text += "You are on the right track but missed key points. ";
  } else {
    text += "That is not quite right. ";
  }
  text += `The correct answer is: ${question.answer}`;
  return text;
}

function updateScore() {
  els.score.textContent = `${state.score} / ${state.questions.length}`;
}

function showQuestion() {
  const q = state.questions[state.index];
  els.questionNum.textContent = `Question ${state.index + 1} of ${state.questions.length}`;
  els.questionText.textContent = q.text;
  els.transcript.textContent = "—";
  els.feedback.textContent = "—";
  els.answerInput.value = "";
  updateScore();
}

function initRecognition() {
  if (!SpeechRecognition || isIOS) return null;

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";
  recognition.maxAlternatives = 1;
  return recognition;
}

function listenOnce(prompt = "Listening...") {
  return new Promise((resolve, reject) => {
    if (!state.recognition) {
      reject(new Error("Speech recognition not available on this device."));
      return;
    }

    setStatus(prompt, true);
    state.listening = true;

    const recognition = state.recognition;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      state.listening = false;
      setStatus("Processing...", false);
      resolve(transcript);
    };

    recognition.onerror = (event) => {
      state.listening = false;
      setStatus("Could not hear you.", false);
      reject(new Error(event.error || "recognition-error"));
    };

    recognition.onend = () => {
      state.listening = false;
    };

    try {
      recognition.start();
    } catch (err) {
      reject(err);
    }
  });
}

function isContinueCommand(text) {
  const n = normalize(text);
  return (
    n === "next" ||
    n.includes("yes") ||
    n.includes("next") ||
    n.includes("continue") ||
    n.includes("move on") ||
    n.includes("go ahead") ||
    n === "ok" ||
    n.includes("okay")
  );
}

function setMode(mode) {
  state.mode = mode;
  els.chatModeBtn.classList.toggle("active", mode === "chat");
  els.voiceModeBtn.classList.toggle("active", mode === "voice");
  els.answerInputRow.style.display = mode === "chat" ? "flex" : "none";

  if (mode === "chat") {
    els.modeHint.innerHTML =
      "<strong>Chat Mode</strong> — read the question, type your answer, tap Submit. Type <strong>next</strong> in the box after feedback. Best for iPhone &amp; Cursor mobile.";
    setStatus("Chat Mode — tap Start Test", false);
  } else {
    els.modeHint.innerHTML =
      "<strong>Voice Mode</strong> — works best on desktop Chrome/Edge. iPhone users: use Chat Mode instead.";
    setStatus("Voice Mode — tap Start Test", false);
  }
}

function waitForTextInput(prompt) {
  return new Promise((resolve) => {
    state.waitingForNext = prompt.includes("next");
    els.answerInput.placeholder = prompt;
    els.answerInput.disabled = false;
    els.submitAnswerBtn.disabled = false;
    els.answerInput.focus();
    setStatus(prompt, false);

    const handler = () => {
      const value = els.answerInput.value.trim();
      if (!value) return;
      els.submitAnswerBtn.removeEventListener("click", handler);
      els.answerInput.removeEventListener("keydown", onKey);
      els.answerInput.disabled = true;
      els.submitAnswerBtn.disabled = true;
      resolve(value);
    };

    const onKey = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handler();
      }
    };

    els.submitAnswerBtn.addEventListener("click", handler);
    els.answerInput.addEventListener("keydown", onKey);
  });
}

async function getAnswer(prompt) {
  if (state.mode === "chat") {
    return waitForTextInput(prompt);
  }
  return listenOnce(prompt);
}

async function waitForContinue() {
  if (state.mode === "chat") {
    els.feedback.textContent += "\n\nType **next** below to continue.";
    const cmd = await waitForTextInput("Type 'next' to continue...");
    return isContinueCommand(cmd);
  }

  await speak("Say yes or next when you are ready for the next question.");
  let confirmed = false;
  while (!confirmed) {
    try {
      const cmd = await listenOnce("Waiting for you to say next...");
      if (isContinueCommand(cmd)) confirmed = true;
      else await speak("Please say yes or next to continue.");
    } catch {
      await speak("I did not catch that. Please say next to continue.");
    }
  }
  return true;
}

async function askCurrentQuestion() {
  const question = state.questions[state.index];
  state.phase = "asking";
  showQuestion();
  log(`Question ${question.id}`);

  if (state.mode === "voice") {
    setStatus("Speaking question...", false);
    await speak(question.text);
    await speak("Please give your answer now.");
  } else {
    setStatus("Read the question and type your answer below.", false);
  }

  state.phase = "listening";
  try {
    const userAnswer = await getAnswer(
      state.mode === "chat" ? "Type your answer here..." : "Listening for your answer..."
    );
    els.transcript.textContent = userAnswer;
    log(`You: ${userAnswer}`, "user");

    state.phase = "feedback";
    const result = gradeAnswer(question, userAnswer);
    const feedbackText = buildFeedback(question, result);
    els.feedback.textContent = feedbackText;
    updateScore();
    log(feedbackText, result.correct ? "success" : "warn");

    if (state.mode === "voice") await speak(feedbackText);

    state.phase = "confirm";
    await waitForContinue();
  } catch (err) {
    log(`Error: ${err.message}`, "error");
    els.feedback.textContent = "Could not get your answer. Try typing in Chat Mode.";
    setStatus("Use Chat Mode on iPhone", false);
    state.phase = "idle";
  }
}

async function runQuiz() {
  els.startBtn.disabled = true;
  els.repeatBtn.disabled = false;
  els.skipBtn.disabled = false;
  els.stopBtn.disabled = true;
  state.quizRunning = true;

  const topic = QUIZ_TOPICS[state.topic];
  state.questions = topic.questions;
  state.index = 0;
  state.score = 0;

  els.topicTitle.textContent = topic.title;
  els.topicLevel.textContent = topic.level;
  updateScore();

  const welcome =
    state.mode === "chat"
      ? `Starting ${topic.title} mock test. ${state.questions.length} questions. Type your answers below.`
      : `Welcome to your mock test on ${topic.title}. ${state.questions.length} questions. Let's begin.`;

  log(welcome);
  setStatus("Test in progress...", false);
  if (state.mode === "voice") await speak(welcome);

  while (state.index < state.questions.length && state.quizRunning) {
    await askCurrentQuestion();
    state.index += 1;
  }

  if (!state.quizRunning) return;

  const summary = `Test complete. Score: ${state.score}/${state.questions.length}. ${
    state.score >= 8
      ? "Excellent! Strong grasp of Collection Framework."
      : state.score >= 5
        ? "Good effort. Review HashMap, fail-fast, and thread-safe collections."
        : "Keep practicing Collection vs Collections, ArrayList vs LinkedList, and Map contracts."
  }`;

  els.questionNum.textContent = "Test Complete";
  els.questionText.textContent = summary;
  els.feedback.textContent = summary;
  log(summary, "success");
  if (state.mode === "voice") await speak(summary);

  finishQuiz();
}

function finishQuiz() {
  setStatus("Test finished", false);
  els.startBtn.disabled = false;
  els.repeatBtn.disabled = true;
  els.skipBtn.disabled = true;
  els.stopBtn.disabled = true;
  els.submitAnswerBtn.disabled = true;
  state.phase = "idle";
  state.quizRunning = false;
}

function stopQuiz() {
  if (state.recognition && state.listening) {
    state.recognition.abort();
  }
  synth.cancel();
  state.quizRunning = false;
  state.phase = "idle";
  finishQuiz();
  log("Test stopped", "warn");
}

function bindEvents() {
  els.startBtn.addEventListener("click", () => {
    if (state.mode === "voice" && !state.recognition) {
      alert("Voice not supported on iPhone. Please use Chat Mode.");
      setMode("chat");
      return;
    }
    runQuiz();
  });

  els.chatModeBtn.addEventListener("click", () => setMode("chat"));
  els.voiceModeBtn.addEventListener("click", () => {
    if (isIOS) {
      alert("iPhone does not support voice input in browser. Chat Mode is recommended.");
      setMode("chat");
      return;
    }
    setMode("voice");
  });

  els.repeatBtn.addEventListener("click", async () => {
    const q = state.questions[state.index];
    if (!q) return;
    if (state.mode === "voice") await speak(q.text);
    else {
      els.questionText.textContent = q.text;
      setStatus("Question repeated — type your answer.", false);
    }
  });

  els.skipBtn.addEventListener("click", async () => {
    if (!state.quizRunning) return;
    log("Skipped question", "warn");
    state.index += 1;
    if (state.index < state.questions.length) {
      await askCurrentQuestion();
      state.index += 1;
    }
  });

  els.stopBtn.addEventListener("click", stopQuiz);
}

function init() {
  state.recognition = initRecognition();
  bindEvents();

  if (isIOS || isMobile) {
    setMode("chat");
    els.voiceModeBtn.disabled = isIOS;
    log("iPhone/mobile detected — Chat Mode enabled (recommended).");
  } else {
    setMode("chat");
    log("Ready. Chat Mode works everywhere. Voice Mode for desktop Chrome/Edge.");
  }
}

document.addEventListener("DOMContentLoaded", init);
