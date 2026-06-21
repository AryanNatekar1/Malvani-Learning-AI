import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("Malvani Learning AI")
print("Type 'exit' to quit")

knowledge = {
    "gravity": "gravity",
    "energy": "energy",
    "force": "force",
    "motion": "motion",
    "newton": "newton",
    "newton law": "newton",
    "newton laws": "newton",
    "acceleration": "motion",
    "velocity": "motion"
}

while True:
    question = input("\nStudent: ").lower()

    if question == "exit":
        print("\nGoodbye!")
        break

    found = False

    for keyword, topic in knowledge.items():

        if keyword in question:

            file_path = os.path.join(
                BASE_DIR,
                "data",
                f"{topic}.txt"
            )

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                print("\nAI:")
                print(content)

            except FileNotFoundError:
                print("\nAI:")
                print(f"Knowledge file missing: {topic}.txt")

            found = True
            break

    if not found:
        print("\nAI:")
        print("I am still learning this topic.")