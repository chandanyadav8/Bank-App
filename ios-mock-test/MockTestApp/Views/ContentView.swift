import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = QuizViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    headerSection
                    statusSection
                    controlButtons
                    questionCard
                    answerCard
                    feedbackCard
                }
                .padding()
            }
            .navigationTitle("Voice Mock Test")
            .navigationBarTitleDisplayMode(.inline)
            .background(Color(.systemGroupedBackground))
        }
    }

    private var headerSection: some View {
        VStack(spacing: 8) {
            Text(QuestionsData.topicTitle)
                .font(.title2.bold())
            Text(QuestionsData.topicLevel)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text("Runs 100% on your iPhone — no server needed")
                .font(.caption)
                .foregroundStyle(.blue)
        }
        .frame(maxWidth: .infinity)
    }

    private var statusSection: some View {
        HStack {
            ZStack {
                Circle()
                    .fill(viewModel.speech.isListening ? Color.blue.opacity(0.2) : Color.gray.opacity(0.15))
                    .frame(width: 56, height: 56)
                Image(systemName: viewModel.speech.isListening ? "mic.fill" : viewModel.speech.isSpeaking ? "speaker.wave.2.fill" : "mic")
                    .font(.title2)
                    .foregroundStyle(viewModel.speech.isListening ? .blue : .primary)
            }
            VStack(alignment: .leading) {
                Text(viewModel.statusMessage)
                    .font(.headline)
                Text(viewModel.progressText)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(viewModel.scoreText)
                .font(.title3.bold())
                .foregroundStyle(.green)
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private var controlButtons: some View {
        VStack(spacing: 12) {
            Button {
                Task { await viewModel.start() }
            } label: {
                Label("Start Voice Test", systemImage: "play.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.phase != .idle && viewModel.phase != .finished)

            HStack(spacing: 12) {
                Button {
                    Task { await viewModel.repeatQuestion() }
                } label: {
                    Label("Repeat", systemImage: "arrow.counterclockwise")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)

                Button {
                    viewModel.stop()
                } label: {
                    Label("Stop", systemImage: "stop.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.red)
            }
        }
    }

    private var questionCard: some View {
        CardView(title: "Current Question") {
            Text(viewModel.questionText)
                .font(.body)
        }
    }

    private var answerCard: some View {
        CardView(title: "Your Answer") {
            if viewModel.speech.isListening {
                Text(viewModel.speech.transcript.isEmpty ? "Listening..." : viewModel.speech.transcript)
                    .foregroundStyle(.blue)
            } else {
                Text(viewModel.userAnswer.isEmpty ? "—" : viewModel.userAnswer)
            }
        }
    }

    private var feedbackCard: some View {
        CardView(title: "Feedback") {
            Text(viewModel.feedbackText.isEmpty ? "—" : viewModel.feedbackText)
        }
    }
}

struct CardView<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title.uppercased())
                .font(.caption)
                .foregroundStyle(.secondary)
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

#Preview {
    ContentView()
}
