/**
 * Java Collection Framework — 3 years experience level
 * Each question has keywords for fuzzy voice-answer matching.
 */
const QUIZ_TOPICS = {
  "java-collection-framework": {
    title: "Java Collection Framework",
    level: "3 years experience",
    questions: [
      {
        id: 1,
        type: "short",
        text: "What is the difference between Collection and Collections in Java? Also name one method from the Collections class.",
        answer:
          "Collection is the root interface in java.util for group objects. Collections is a utility class with static methods like sort, synchronizedList, unmodifiableList, and reverse.",
        keywords: [
          ["collection", "interface"],
          ["collections", "utility", "class", "static"],
          ["sort", "synchronized", "unmodifiable", "reverse", "shuffle", "empty"],
        ],
        minKeywordGroups: 2,
      },
      {
        id: 2,
        type: "mcq",
        text: "Which collection gives O(1) average time for get by index? A: ArrayList. B: LinkedList. C: HashSet. D: TreeSet.",
        options: { A: "ArrayList", B: "LinkedList", C: "HashSet", D: "TreeSet" },
        correct: "A",
        answer: "ArrayList gives O(1) average time for get by index because it is backed by a dynamic array.",
      },
      {
        id: 3,
        type: "short",
        text: "What is the default initial capacity of an ArrayList in Java?",
        answer: "The default initial capacity of ArrayList is 10 elements.",
        keywords: [["10", "ten"]],
        minKeywordGroups: 1,
      },
      {
        id: 4,
        type: "short",
        text: "Explain fail-fast behavior in Java collections. Which exception is thrown?",
        answer:
          "Fail-fast iterators throw ConcurrentModificationException when the collection is structurally modified during iteration outside the iterator's own remove method. Examples include ArrayList and HashMap iterators.",
        keywords: [
          ["fail", "fast", "failfast"],
          ["concurrentmodification", "concurrent modification"],
          ["iteration", "iterate", "modified"],
        ],
        minKeywordGroups: 2,
      },
      {
        id: 5,
        type: "mcq",
        text: "Which Map implementation maintains insertion order? A: HashMap. B: TreeMap. C: LinkedHashMap. D: Hashtable.",
        options: { A: "HashMap", B: "TreeMap", C: "LinkedHashMap", D: "Hashtable" },
        correct: "C",
        answer: "LinkedHashMap maintains insertion order of keys. TreeMap sorts by key order.",
      },
      {
        id: 6,
        type: "short",
        text: "Why must you override both equals and hashCode when using objects as HashMap keys?",
        answer:
          "hashCode determines the bucket. equals determines key equality within the bucket. If equals is overridden without hashCode, equal objects may land in different buckets and break Map contract.",
        keywords: [
          ["equals", "hashcode", "hash code"],
          ["bucket", "contract"],
          ["map", "hashmap", "key"],
        ],
        minKeywordGroups: 2,
      },
      {
        id: 7,
        type: "mcq",
        text: "Which is thread-safe without external synchronization? A: HashMap. B: ConcurrentHashMap. C: ArrayList. D: HashSet.",
        options: { A: "HashMap", B: "ConcurrentHashMap", C: "ArrayList", D: "HashSet" },
        correct: "B",
        answer: "ConcurrentHashMap is designed for concurrent access. HashMap, ArrayList, and HashSet are not thread-safe by default.",
      },
      {
        id: 8,
        type: "short",
        text: "What is the difference between Comparable and Comparator?",
        answer:
          "Comparable is implemented by the class itself via compareTo for natural ordering. Comparator is a separate strategy via compare method, useful for multiple sort orders.",
        keywords: [
          ["comparable", "compareto", "natural"],
          ["comparator", "compare", "strategy", "external"],
        ],
        minKeywordGroups: 2,
      },
      {
        id: 9,
        type: "short",
        text: "Can a HashSet contain duplicate elements? What happens if you add the same element twice?",
        answer:
          "No. HashSet does not allow duplicates. Adding the same element again is ignored and add returns false.",
        keywords: [
          ["no", "not", "duplicate", "unique"],
          ["ignore", "false", "reject", "unchanged"],
        ],
        minKeywordGroups: 1,
      },
      {
        id: 10,
        type: "short",
        text: "Name two differences between ArrayDeque and Stack for LIFO operations.",
        answer:
          "ArrayDeque is faster, not synchronized, and implements Deque. Stack extends Vector, is legacy, synchronized, and slower. Prefer ArrayDeque over Stack.",
        keywords: [
          ["arraydeque", "deque", "faster", "not synchronized", "legacy"],
          ["stack", "vector", "synchronized", "slow"],
        ],
        minKeywordGroups: 1,
      },
    ],
  },
};
