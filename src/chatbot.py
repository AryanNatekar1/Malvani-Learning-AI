print("Malvani Learning AI Prototype")
print("Type 'exit' to quit")

knowledge = {
    "gravity": "Gravity is the force that pulls objects toward Earth.",
    "newton": "Newton's laws explain how objects move when forces act on them.",
    "energy": "Energy is the ability to do work or cause change.",
    "force": "A force is a push or pull acting on an object.",
    "motion": "Motion is the change in position of an object over time."
}

while True:
    question = input("\nStudent: ").lower()

    if question == "exit":
        break

    found = False

    for topic in knowledge:
        if topic in question:
            print("\nAI:")
            print(knowledge[topic])
            found = True
            break

    if not found:
        print("\nAI:")
        print("I am still learning this topic.")