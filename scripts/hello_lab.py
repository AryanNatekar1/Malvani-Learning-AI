import os

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
            with open(f"data/{topic}.txt", "r", encoding="utf-8") as f:
                print("\nAI:")
                print(f.read())

            found = True
            break

    if not found:
        print("\nAI:")
        print("I am still learning this topic.")