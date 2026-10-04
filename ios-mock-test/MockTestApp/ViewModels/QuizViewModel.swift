import Foundation

enum QuizPhase: Equatable {
    case idle
    case asking
    case listening
    case feedback
    case waitingForNext
    case finished
}

@MainActor
final class QuizViewModel: ObservableObject {
    @Published var phase: QuizPhase = .idle
    @Published var currentIndex = 0
    @Published var score = 0
    @Published var questionText = "Tap Start to begin your voice mock test."
    @Published var userAnswer = ""
    @Published var feedbackText = ""
    @Published var statusMessage = "Ready"

    let speech = SpeechManager()
    private let questions = QuestionsData.questions

    var progressText: String {
        if phase == .finished {
            return "Test Complete"
        }
        return "Question \(min(currentIndex + 1, questions.count)) of \(questions.count)"
    }

    var scoreText: String {
        "\(score) / \(questions.count)"
    }

    func start() async {
        await speech.requestPermissions()
        guard speech.permissionGranted else { return }

        currentIndex = 0
        score = 0
        phase = .asking
        statusMessage = "Starting test..."

        await speech.speak(
            "Welcome to your mock test on \(QuestionsData.topicTitle). " +
            "There are \(questions.count) questions. I will ask each question, listen for your answer, correct you, and move on when you say next. Let's begin."
        )

        await askCurrentQuestion()
    }

    func askCurrentQuestion() async {
        guard currentIndex < questions.count else {
            await finishQuiz()
            return
        }

        let question = questions[currentIndex]
        phase = .asking
        questionText = question.text
        userAnswer = ""
        feedbackText = ""
        statusMessage = "Speaking question..."

        await speech.speak(question.text)
        await speech.speak("Please give your answer now.")

        phase = .listening
        statusMessage = "Listening..."

        let answer = await speech.listen()
        userAnswer = answer ?? ""
        statusMessage = "Processing answer..."

        let result = Question.grade(question, userAnswer: userAnswer)
        if result.verdict == .correct {
            score += 1
        }

        var feedback = "Verdict: \(result.verdict.rawValue). "
        switch result.verdict {
        case .correct:
            feedback += "Well done. "
        case .partial:
            feedback += "You are on the right track but missed key points. "
        case .incorrect:
            feedback += "That is not quite right. "
        }
        feedback += "The correct answer is: \(question.answer)"

        feedbackText = feedback
        phase = .feedback
        statusMessage = "Feedback"

        await speech.speak(feedback)
        await speech.speak("Say next when you are ready for the next question.")

        phase = .waitingForNext
        statusMessage = "Say 'next' to continue..."

        var confirmed = false
        while !confirmed {
            let cmd = await speech.listen()
            let text = (cmd ?? "").lowercased()
            if text.contains("next") || text.contains("yes") || text.contains("continue") || text.contains("ok") {
                confirmed = true
            } else {
                await speech.speak("Please say next to continue.")
            }
        }

        currentIndex += 1
        await askCurrentQuestion()
    }

    func finishQuiz() async {
        phase = .finished
        let summary: String
        if score >= 8 {
            summary = "Test complete. Your score is \(score) out of \(questions.count). Excellent work!"
        } else if score >= 5 {
            summary = "Test complete. Your score is \(score) out of \(questions.count). Good effort. Review HashMap, fail-fast, and thread-safe collections."
        } else {
            summary = "Test complete. Your score is \(score) out of \(questions.count). Keep practicing Collection versus Collections and Map contracts."
        }
        questionText = summary
        feedbackText = summary
        statusMessage = "Finished"
        await speech.speak(summary)
    }

    func repeatQuestion() async {
        guard currentIndex < questions.count else { return }
        await speech.speak(questions[currentIndex].text)
    }

    func stop() {
        speech.stopSpeaking()
        speech.stopListening()
        phase = .idle
        statusMessage = "Stopped"
    }
}
