"""Terminal interface for the local Malvani Learning AI prototype."""

from knowledge_engine import find_topic, load_student_lesson


def run_chatbot() -> None:
    """Run the terminal chatbot until the student types ``exit``."""
    print("Malvani Learning AI")
    print("Type 'exit' to quit")

    while True:
        question = input("\nStudent: ")

        if question.lower() == "exit":
            print("\nGoodbye!")
            break

        topic = find_topic(question)
        if topic is None:
            print("\nAI:")
            print("I am still learning this topic.")
            continue

        content = load_student_lesson(topic)
        print("\nAI:")
        if content is None:
            print(f"Knowledge file missing: {topic}.txt")
        else:
            print(content)


if __name__ == "__main__":
    run_chatbot()
