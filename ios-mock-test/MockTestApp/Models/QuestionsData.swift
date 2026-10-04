import Foundation

enum QuestionsData {
    static let topicTitle = "Java Collection Framework"
    static let topicLevel = "3 years experience"

    static let questions: [Question] = [
        Question(
            id: 1, type: .shortAnswer,
            text: "What is the difference between Collection and Collections in Java? Also name one method from the Collections class.",
            answer: "Collection is the root interface in java.util for group objects. Collections is a utility class with static methods like sort, synchronizedList, unmodifiableList, and reverse.",
            correctOption: nil,
            keywordGroups: [
                ["collection", "interface"],
                ["collections", "utility", "class", "static"],
                ["sort", "synchronized", "unmodifiable", "reverse", "shuffle"]
            ],
            minKeywordGroups: 2
        ),
        Question(
            id: 2, type: .mcq,
            text: "Which collection gives O(1) average time for get by index? A: ArrayList. B: LinkedList. C: HashSet. D: TreeSet.",
            answer: "ArrayList gives O(1) average time for get by index because it is backed by a dynamic array.",
            correctOption: "a",
            keywordGroups: [], minKeywordGroups: 0
        ),
        Question(
            id: 3, type: .shortAnswer,
            text: "What is the default initial capacity of an ArrayList in Java?",
            answer: "The default initial capacity of ArrayList is 10 elements.",
            correctOption: nil,
            keywordGroups: [["10", "ten"]],
            minKeywordGroups: 1
        ),
        Question(
            id: 4, type: .shortAnswer,
            text: "Explain fail-fast behavior in Java collections. Which exception is thrown?",
            answer: "Fail-fast iterators throw ConcurrentModificationException when the collection is structurally modified during iteration outside the iterator's own remove method.",
            correctOption: nil,
            keywordGroups: [
                ["fail", "fast"],
                ["concurrentmodification", "concurrent modification"],
                ["iteration", "iterate", "modified"]
            ],
            minKeywordGroups: 2
        ),
        Question(
            id: 5, type: .mcq,
            text: "Which Map implementation maintains insertion order? A: HashMap. B: TreeMap. C: LinkedHashMap. D: Hashtable.",
            answer: "LinkedHashMap maintains insertion order of keys. TreeMap sorts by key order.",
            correctOption: "c",
            keywordGroups: [], minKeywordGroups: 0
        ),
        Question(
            id: 6, type: .shortAnswer,
            text: "Why must you override both equals and hashCode when using objects as HashMap keys?",
            answer: "hashCode determines the bucket. equals determines key equality within the bucket. If equals is overridden without hashCode, equal objects may land in different buckets.",
            correctOption: nil,
            keywordGroups: [
                ["equals", "hashcode", "hash code"],
                ["bucket", "contract"],
                ["map", "hashmap", "key"]
            ],
            minKeywordGroups: 2
        ),
        Question(
            id: 7, type: .mcq,
            text: "Which is thread-safe without external synchronization? A: HashMap. B: ConcurrentHashMap. C: ArrayList. D: HashSet.",
            answer: "ConcurrentHashMap is designed for concurrent access. HashMap, ArrayList, and HashSet are not thread-safe by default.",
            correctOption: "b",
            keywordGroups: [], minKeywordGroups: 0
        ),
        Question(
            id: 8, type: .shortAnswer,
            text: "What is the difference between Comparable and Comparator?",
            answer: "Comparable is implemented by the class itself via compareTo for natural ordering. Comparator is a separate strategy via compare method for multiple sort orders.",
            correctOption: nil,
            keywordGroups: [
                ["comparable", "compareto", "natural"],
                ["comparator", "compare", "strategy", "external"]
            ],
            minKeywordGroups: 2
        ),
        Question(
            id: 9, type: .shortAnswer,
            text: "Can a HashSet contain duplicate elements? What happens if you add the same element twice?",
            answer: "No. HashSet does not allow duplicates. Adding the same element again is ignored and add returns false.",
            correctOption: nil,
            keywordGroups: [
                ["no", "not", "duplicate", "unique"],
                ["ignore", "false", "reject", "unchanged"]
            ],
            minKeywordGroups: 1
        ),
        Question(
            id: 10, type: .shortAnswer,
            text: "Name two differences between ArrayDeque and Stack for LIFO operations.",
            answer: "ArrayDeque is faster, not synchronized, and implements Deque. Stack extends Vector, is legacy, synchronized, and slower. Prefer ArrayDeque over Stack.",
            correctOption: nil,
            keywordGroups: [
                ["arraydeque", "deque", "faster", "legacy"],
                ["stack", "vector", "synchronized"]
            ],
            minKeywordGroups: 1
        )
    ]
}
