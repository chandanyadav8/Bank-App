const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;

const state = {
  topic: "java-collection-framework",
  questions: [],
  index: 0,
  score: 0,
  phase: "idle", // idle | asking | listening | feedback | confirm
  recognition: null,
  listening: false,
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
    if (!synth) {
      resolve();
      return;
    }
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
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

function buildFeedback(question, result, userAnswer) {
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
  updateScore();
}

function initRecognition() {
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-IN";
  recognition.maxAlternatives = 1;
  return recognition;
}

function listenOnce(prompt = "Listening for your answer...") {
  return new Promise((resolve, reject) => {
    if (!state.recognition) {
      reject(new Error("Speech recognition is not supported in this browser."));
      return;
    }

    setStatus(prompt, true);
    state.listening = true;

    const recognition = state.recognition;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      state.listening = false;
      setStatus("Processing your answer...", false);
      resolve(transcript);
    };

    recognition.onerror = (event) => {
      state.listening = false;
      setStatus("Could not hear you. Try again.", false);
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
    n.includes("yes") ||
    n.includes("next") ||
    n.includes("continue") ||
    n.includes("move on") ||
    n.includes("go ahead") ||
    n.includes("ok") ||
    n.includes("okay")
  );
}

async function askCurrentQuestion() {
  const question = state.questions[state.index];
  state.phase = "asking";
  showQuestion();
  log(`Speaking question ${question.id}`);
  setStatus("Speaking question...", false);
  await speak(question.text);
  await speak("Please give your answer now.");

  state.phase = "listening";
  try {
    const userAnswer = await listenOnce("Listening for your answer...");
    els.transcript.textContent = userAnswer;
    log(`You said: ${userAnswer}`, "user");

    state.phase = "feedback";
    const result = gradeAnswer(question, userAnswer);
    const feedbackText = buildFeedback(question, result, userAnswer);
    els.feedback.textContent = feedbackText;
    updateScore();
    log(feedbackText, result.correct ? "success" : "warn");

    await speak(feedbackText);
    await speak("Say yes or next when you are ready for the next question.");

    state.phase = "confirm";
    let confirmed = false;
    while (!confirmed) {
      try {
        const cmd = await listenOnce("Waiting for you to say next...");
        els.transcript.textContent = cmd;
        if (isContinueCommand(cmd)) {
          confirmed = true;
        } else {
          await speak("Please say yes or next to continue.");
        }
      } catch {
        await speak("I did not catch that. Please say next to continue.");
      }
    }
  } catch (err) {
    log(`Listen error: ${err.message}`, "error");
    els.feedback.textContent = "Could not hear your answer. Use Repeat Question or try again.";
    setStatus("Listen failed — use Repeat or Skip", false);
    state.phase = "idle";
    return;
  }
}

async function runQuiz() {
  els.startBtn.disabled = true;
  els.repeatBtn.disabled = false;
  els.skipBtn.disabled = false;
  els.stopBtn.disabled = false;

  const topic = QUIZ_TOPICS[state.topic];
  state.questions = topic.questions;
  state.index = 0;
  state.score = 0;

  els.topicTitle.textContent = topic.title;
  els.topicLevel.textContent = topic.level;
  updateScore();

  await speak(
    `Welcome to your mock test on ${topic.title}. There are ${state.questions.length} questions. I will ask each question, wait for your spoken answer, correct you, and then move to the next question when you say next. Let's begin.`
  );

  while (state.index < state.questions.length) {
    await askCurrentQuestion();
    state.index += 1;
  }

  const summary = `Test complete. Your score is ${state.score} out of ${state.questions.length}. ${
    state.score >= 8
      ? "Excellent work. You have a strong grasp of the Java Collection Framework."
      : state.score >= 5
        ? "Good effort. Review HashMap internals, fail-fast behavior, and thread-safe collections."
        : "Keep practicing. Focus on Collection versus Collections, ArrayList versus LinkedList, and Map contracts."
  }`;
  els.questionNum.textContent = "Test Complete";
  els.questionText.textContent = summary;
  els.feedback.textContent = summary;
  log(summary, "success");
  await speak(summary);

  setStatus("Test finished", false);
  els.startBtn.disabled = false;
  els.repeatBtn.disabled = true;
  els.skipBtn.disabled = true;
  els.stopBtn.disabled = true;
  state.phase = "idle";
}

function stopQuiz() {
  if (state.recognition && state.listening) {
    state.recognition.abort();
  }
  synth.cancel();
  state.phase = "idle";
  setStatus("Stopped", false);
  els.startBtn.disabled = false;
  log("Quiz stopped by user", "warn");
}

function checkSupport() {
  const issues = [];
  if (!SpeechRecognition) {
    issues.push("Speech Recognition is not supported. Use Chrome or Edge.");
  }
  if (!synth) {
    issues.push("Speech Synthesis is not supported in this browser.");
  }
  if (!window.isSecureContext && location.hostname !== "localhost") {
    issues.push("Microphone access requires HTTPS or localhost.");
  }
  return issues;
}

function bindEvents() {
  els.startBtn.addEventListener("click", () => {
    const issues = checkSupport();
    if (issues.length) {
      alert(issues.join("\n"));
      return;
    }
    runQuiz();
  });

  els.repeatBtn.addEventListener("click", async () => {
    if (state.phase === "idle" && state.questions.length) {
      const q = state.questions[state.index] || state.questions[state.questions.length - 1];
      await speak(q.text);
    }
  });

  els.skipBtn.addEventListener("click", () => {
    if (state.index < state.questions.length) {
      log("Skipped to next question", "warn");
      state.index += 1;
      if (state.index < state.questions.length) {
        askCurrentQuestion();
      }
    }
  });

  els.stopBtn.addEventListener("click", stopQuiz);
}

function init() {
  state.recognition = initRecognition();
  bindEvents();

  const issues = checkSupport();
  if (issues.length) {
    setStatus(issues[0], false);
    log(issues.join(" "), "error");
  } else {
    setStatus('Ready — click "Start Voice Test"', false);
    log("Voice assistant ready. Allow microphone access when prompted.");
  }
}

document.addEventListener("DOMContentLoaded", init);
