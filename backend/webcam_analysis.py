import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import json
import os

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "webcam_results.json")


def write_results(data: dict):
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f)


def compute_stress_label(ear: float, smile: float, looking_away: bool) -> str:
    if looking_away:
        return "Distracted"
    if smile > 0.4:
        return "Confident"
    if ear < 0.28:
        return "Tense"
    if ear >= 0.28 and smile < 0.15:
        return "Focused"
    return "Neutral"


def run():
    base_options = python.BaseOptions(model_asset_path="face_landmarker.task")
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        output_face_blendshapes=True,
    )
    detector = vision.FaceLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_image)

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]

            # Eye Aspect Ratio — blink/eye openness detection
            ear = abs(landmarks[159].y - landmarks[145].y) / \
                  max(abs(landmarks[33].x - landmarks[133].x), 0.001)
            blink = ear < 0.2

            # Smile score from blendshapes
            smile = 0.0
            if result.face_blendshapes:
                shapes = {s.category_name: s.score for s in result.face_blendshapes[0]}
                smile = shapes.get("mouthSmileLeft", 0.0)

            # Face direction — nose tip x position
            nose_x = landmarks[1].x
            looking_away = nose_x < 0.35 or nose_x > 0.65

            stress_label = compute_stress_label(ear, smile, looking_away)

            write_results({
                "blink": blink,
                "ear": round(ear, 3),
                "smile": round(float(smile), 3),
                "looking_away": looking_away,
                "stress_label": stress_label,
                "ready": True,
            })

            # Overlay on webcam window
            cv2.putText(frame, f"EAR:  {ear:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            cv2.putText(frame, f"Smile: {smile:.2f}", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            cv2.putText(frame, f"Status: {stress_label}", (10, 86),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

        else:
            write_results({"ready": False})

        cv2.imshow("Interview Monitor", frame)
        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()