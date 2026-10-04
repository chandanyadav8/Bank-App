import Foundation

enum QuestionType {
    case mcq
    case shortAnswer
}

struct Question: Identifiable {
    let id: Int
    let type: QuestionType
    let text: String
    let answer: String
    let correctOption: String?
    let keywordGroups: [[String]]
    let minKeywordGroups: Int

    static func grade(_ question: Question, userAnswer: String) -> GradeResult {
        let normalized = userAnswer.lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespaces)

        guard !normalized.isEmpty else {
            return GradeResult(verdict: .incorrect, matchedGroups: 0)
        }

        if question.type == .mcq {
            let choice = extractMCQChoice(from: normalized)
            let correct = choice == question.correctOption?.lowercased()
            return GradeResult(verdict: correct ? .correct : .incorrect, matchedGroups: correct ? 1 : 0)
        }

        var matched = 0
        for group in question.keywordGroups {
            if group.contains(where: { normalized.contains($0.lowercased()) }) {
                matched += 1
            }
        }

        if matched >= question.minKeywordGroups {
            return GradeResult(verdict: .correct, matchedGroups: matched)
        }
        if matched > 0 {
            return GradeResult(verdict: .partial, matchedGroups: matched)
        }
        return GradeResult(verdict: .incorrect, matchedGroups: 0)
    }

    private static func extractMCQChoice(from text: String) -> String? {
        let patterns = ["option a", "option b", "option c", "option d", "answer a", "answer b", "answer c", "answer d"]
        for (i, letter) in ["a", "b", "c", "d"].enumerated() {
            if text.contains(patterns[i]) || text == letter || text.hasPrefix("\(letter) ") {
                return letter
            }
        }
        let names: [String: String] = [
            "arraylist": "a", "linkedlist": "b", "hashset": "c", "treeset": "d",
            "hashmap": "a", "treemap": "b", "linkedhashmap": "c", "hashtable": "d",
            "concurrenthashmap": "b"
        ]
        for (name, letter) in names where text.contains(name) {
            return letter
        }
        return nil
    }
}

struct GradeResult {
    enum Verdict: String {
        case correct = "Correct"
        case partial = "Partially correct"
        case incorrect = "Incorrect"
    }

    let verdict: Verdict
    let matchedGroups: Int
}
