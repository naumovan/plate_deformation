import io
import pickle
import requests
import cv2
import PIL.Image


def test_flow_single_request():
    image_path = "fixtures/0b90c1c74d46abf7.jpg"
    image = PIL.Image.open(image_path)
    with io.BytesIO() as byte_stream:
        image.save(byte_stream, format='JPEG')
        image_bytes = byte_stream.getvalue()
    files = {'file': ('filename', image_bytes)}
    r = requests.post('http://127.0.0.1:8000/', files=files, timeout=20)
    print("Plate = ", r.headers["X-Text"])
    image = PIL.Image.open(io.BytesIO(r.content))
    image.show()
