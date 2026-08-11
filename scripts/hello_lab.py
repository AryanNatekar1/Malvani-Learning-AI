"""Historical terminal experiment using the current safe student lesson renderer."""

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from knowledge_engine import load_student_lesson

print("Malvani Learning AI")
print("Type exit to quit")

while True:
    question = input("\nStudent: ").lower()

    if question == "exit":
        break

    found = False

    topics = ["gravity", "energy", "force", "motion", "newton"]

    for topic in topics:
        if topic in question:
            content = load_student_lesson(topic)
            print("\nAI:")
            if content is None:
                print(f"Knowledge file missing: {topic}.txt")
            else:
                print(content)

            found = True
            break

    if not found:
        print("\nAI:")
        print("I am still learning this topic.")
