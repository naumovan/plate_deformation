import cv2
import matplotlib.pyplot as plt
import easyocr
from PIL import Image, ImageDraw
import numpy as np
import os
from ultralytics import YOLO

def extract_and_process_crops(image):
    """
    Функция для извлечения и обработки кропов с использованием предобученной модели YOLO.

    Args:
        image_path (str): Путь к изображению.

    Returns:
        list: Список изображений (кропов), извлеченных с использованием модели YOLO.
    """
    if image is None:
        print(f"Ошибка чтения изображения {image_path}")
        return []

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_height, image_width, _ = image_rgb.shape
    model_weights = 'weights/best.pt'
    model = YOLO(model_weights, task='detect')
    results = model.predict(image_rgb, device='cpu', conf=0.30, iou=0.45)

    preds = results[0].boxes.cpu().numpy()

    # Преобразование bounding box'ов и сортировка по x_min
    bounding_boxes = []
    for pred in preds:
        bbox = pred.xyxy[0]  # Извлечение координат bounding box'а
        class_id = int(pred.cls)  # Идентификатор класса
        x_min, y_min, x_max, y_max = map(int, bbox)
        bounding_boxes.append((x_min, y_min, x_max, y_max, class_id))

    # Сортировка bounding box'ов по x_min (по возрастанию)
    bounding_boxes.sort(key=lambda bbox: bbox[0])

    cropped_images = []
    for idx, (x_min, y_min, x_max, y_max, class_id) in enumerate(bounding_boxes):
        # Извлечение кропа
        bbox_image = image_rgb[y_min:y_max, x_min:x_max]
        cropped_images.append(bbox_image)

    return cropped_images


def detect_symbols(cropped_images, target_size=(89, 154)):
    # Создание объекта Reader
    reader = easyocr.Reader(['en'])

    recognized_texts = []
    for idx, crop_image in enumerate(cropped_images):
        # Изменение размера кропа до заданного
        resized_crop = cv2.resize(crop_image, target_size, interpolation=cv2.INTER_AREA)

        # Преобразование кропа в формат, совместимый с EasyOCR
        crop_image_rgb = cv2.cvtColor(resized_crop, cv2.COLOR_RGB2BGR)

        # Установка allowlist в зависимости от индекса
        if idx in [0, 4, 5]:  # Индексы 0, 4 и 5 (первый, пятый и шестой кроп)
            allowlist = 'ABEKMHOPCTYX'
            default_value = 'C'
        else:  # Остальные кропы
            allowlist = '1234567890'
            default_value = '7'

        results = reader.readtext(crop_image_rgb, detail=0, allowlist=allowlist)

        if results:
            recognized_text = results[0]
        else:
            recognized_text = default_value

        recognized_texts.append(recognized_text)
        print(f"Обнаруженный текст: {recognized_text}")

    # Объединение текста
    final_text = ''.join(recognized_texts)
    print(f"Итоговая строка: {final_text}")

    return final_text

def postprocess_symbols(final_text):
    template_width = 512
    template_height = 112
    background_color = 'white'

    symbols_folder = "numbers"

    template = Image.new('RGB', (template_width, template_height), background_color)
    draw = ImageDraw.Draw(template)

    def place_symbol(image_path, position):
        symbol_image = Image.open(image_path)
        symbol_image = symbol_image.resize((int(position['width']), int(position['height'])))
        template.paste(symbol_image, (int(position['x']), int(position['y'])))

    # Определение позиций символов на шаблоне
    symbol_positions = [
        {'pos': 1, 'p1': (0.05, 0.250), 'p2': (0.16, 0.92)},
        {'pos': 2, 'p1': (0.16, 0.100), 'p2': (0.27, 0.92)},
        {'pos': 3, 'p1': (0.265, 0.100), 'p2': (0.375, 0.92)},
        {'pos': 4, 'p1': (0.37, 0.100), 'p2': (0.48, 0.92)},
        {'pos': 5, 'p1': (0.475, 0.250), 'p2': (0.585, 0.92)},
        {'pos': 6, 'p1': (0.58, 0.250), 'p2': (0.69, 0.92)},
        {'pos': 7, 'p1': (0.71, 0.05), 'p2': (0.795, 0.7)},
        {'pos': 8, 'p1': (0.79, 0.05), 'p2': (0.875, 0.7)},
        {'pos': 9, 'p1': (0.87, 0.05), 'p2': (0.96, 0.7)}
    ]

    two_digit_region_template = [
        {'pos': 1, 'p1': (0.067, 0.250), 'p2': (0.177, 0.92)},
        {'pos': 2, 'p1': (0.19, 0.100), 'p2': (0.3, 0.92)},
        {'pos': 3, 'p1': (0.3, 0.100), 'p2': (0.41, 0.92)},
        {'pos': 4, 'p1': (0.41, 0.100), 'p2': (0.52, 0.92)},
        {'pos': 5, 'p1': (0.53, 0.250), 'p2': (0.64, 0.92)},
        {'pos': 6, 'p1': (0.64, 0.250), 'p2': (0.75, 0.92)},
        {'pos': 7, 'p1': (0.77, 0.05), 'p2': (0.86, 0.7)},
        {'pos': 8, 'p1': (0.86, 0.05), 'p2': (0.95, 0.7)}
    ]

    # Размещение каждого символа на шаблоне
    for symbol_index, char in enumerate(final_text):
        if len(final_text) > 8:
            for pos_info in symbol_positions:
                if pos_info['pos'] == symbol_index + 1:
                    p1_x, p1_y = pos_info['p1'][0] * template_width, pos_info['p1'][1] * template_height
                    p2_x, p2_y = pos_info['p2'][0] * template_width, pos_info['p2'][1] * template_height
                    symbol_width = p2_x - p1_x
                    symbol_height = p2_y - p1_y

                    image_path = os.path.join(symbols_folder, f"{char}.png")
                    symbol_image = Image.open(image_path)
                    symbol_image = symbol_image.resize((int(symbol_width), int(symbol_height)))

                    # Размещение символа на шаблоне
                    template.paste(symbol_image, (int(p1_x), int(p1_y)))
        elif len(final_text) == 8:
            symbol_positions = two_digit_region_template
            for pos_info in symbol_positions:
                if pos_info['pos'] == symbol_index + 1:
                    p1_x, p1_y = pos_info['p1'][0] * template_width, pos_info['p1'][1] * template_height
                    p2_x, p2_y = pos_info['p2'][0] * template_width, pos_info['p2'][1] * template_height
                    symbol_width = p2_x - p1_x
                    symbol_height = p2_y - p1_y

                    image_path = os.path.join(symbols_folder, f"{char}.png")
                    symbol_image = Image.open(image_path)
                    symbol_image = symbol_image.resize((int(symbol_width), int(symbol_height)))

                    # Размещение символа на шаблоне
                    template.paste(symbol_image, (int(p1_x), int(p1_y)))
    return template

''' example call
image_path = "/Users/user/Downloads/51_anno/obj_train_data/images/train/0b90c1c74d46abf7.jpg"
mage = cv2.imread(image_path)
cropped_images = extract_and_process_crops(image)

final_text = detect_symbols(cropped_images)
postprocess_symbols(final_text)
'''
