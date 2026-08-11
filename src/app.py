"""Run the Malvani Learning AI desktop application."""

from gui import LearningApp


def main() -> None:
    """Start the local Tkinter interface."""
    app = LearningApp()
    app.mainloop()


if __name__ == "__main__":
    main()
