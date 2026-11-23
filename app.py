import tkinter as tk

from ui import AppView


def main() -> None:
    root = tk.Tk()
    AppView(root)
    root.mainloop()


if __name__ == "__main__":
    main()
