import io
import pickle
import requests
import cv2
import PIL.Image


def test_flow_single_request():
    image_path = "fixtures/0b90c1c74d46abf7.jpg"
    image = cv2.imread(image_path)
    image_bytes = pickle.dumps(image)
    files = {'file': ('filename', image_bytes)}
    r = requests.post('http://127.0.0.1:8000/', files=files, timeout=20)
    print("Plate = ", r.headers["X-Text"])
    image = PIL.Image.open(io.BytesIO(r.content))
    image.show()
