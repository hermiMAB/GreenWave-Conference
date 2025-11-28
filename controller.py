from storage import data_store
from gui import GreenWaveApp

if __name__ == "__main__":
    # Load persistence data at startup
    data_store.load_all()

    # Initialize Main App
    app = GreenWaveApp()

    # Start the GUI Loop
    app.mainloop()