import cv2
import time
import os
import sys
from datetime import datetime
from winotify import Notification, audio
import winsound
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import pyautogui
from deepface import DeepFace



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



camera = cv2.VideoCapture(0)

cascade_path = resource_path("haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(cascade_path)

print("Cascade path:", cascade_path)
print("Cascade loaded:", not face_cascade.empty())


if not os.path.exists("images"):
    os.makedirs("images")

sound_playing = False
overlay_active = False
last_alert_time = 0


def show_notification():
    toast = Notification(
        app_id="AI Security",
        title="🚨 ALERT!",
        msg="Intruder detected!",
        duration="short"
    )
    toast.set_audio(audio.LoopingAlarm, loop=False)
    toast.show()


def show_blur_overlay():
    global overlay_active
    if overlay_active:
        return

    overlay_active = True

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)

    screenshot = pyautogui.screenshot()
    blurred = screenshot.filter(ImageFilter.GaussianBlur(25))

    img = ImageTk.PhotoImage(blurred)
    label = tk.Label(root, image=img)
    label.pack()

    root.after(2500, lambda: (root.destroy(), reset_overlay()))
    root.mainloop()


def reset_overlay():
    global overlay_active
    overlay_active = False



while True:
    ret, frame = camera.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    intruder_detected = False

    for (x, y, w, h) in faces:

        face_img = frame[y:y+h, x:x+w]

        
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

        try:
         owner_path = resource_path("faces/owner.jpg")

         print("Owner path:", owner_path)

         owner_path = resource_path("faces/owner.jpg")
         result = DeepFace.verify(
         face_img,
         owner_path
            )

         if result["verified"] and result["distance"] < 0.6:
                text = "OWNER"
                color = (0, 255, 0)
         else:
                text = "INTRUDER"
                color = (0, 0, 255)
                intruder_detected = True

        except Exception as e:
            print("DeepFace Error:", e)   
            text = "NO FACE"
            color = (255, 255, 0)

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, text, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


   

    if intruder_detected:

        if not sound_playing:
            winsound.PlaySound("SystemExclamation",
                               winsound.SND_ASYNC | winsound.SND_LOOP)
            sound_playing = True

        if time.time() - last_alert_time > 4:
         last_alert_time = time.time()

       
        filename = f"images/intruder_{datetime.now().strftime('%H%M%S')}.jpg"

        
        cv2.imwrite(filename, frame)

        
        import sqlite3

        conn = sqlite3.connect("database/security.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO logs (date, time, status, image_path)
        VALUES (?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            "Detected",
            filename
        ))

        conn.commit()
        conn.close()

        show_notification()
        show_blur_overlay()

    else:
        if sound_playing:
            winsound.PlaySound(None, winsound.SND_PURGE)
            sound_playing = False

    cv2.imshow("FINAL AI SECURITY SYSTEM", frame)

    if cv2.waitKey(1) == 27:
        break

camera.release()
cv2.destroyAllWindows()