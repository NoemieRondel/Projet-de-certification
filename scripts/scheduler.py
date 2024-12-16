import schedule
import time
import subprocess


def run_runner():
    subprocess.run(["python", "runner.py"])


# Planification
schedule.every().day.at("08:00").do(run_runner)  # Tous les jours à 8h
schedule.every().day.at("20:00").do(run_runner)  # Tous les jours à 20h

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
