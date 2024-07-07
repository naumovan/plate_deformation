from os import getenv

import requests
import streamlit as st

host = getenv("BACKEND_HOST", "http://localhost:8000/")


def main():
    st.set_page_config(
        page_title="Детекция номеров автомобилей",
        page_icon="🚘",
        layout="wide",
    )

    st.title("🚘 Детекция номеров автомобилей")
    st.subheader("Цифровой прорыв, команда `tobytes()`")

    image = st.file_uploader("Загрузить изображение", type=["png", "jpg", "jpeg"])
    left, middle, right = st.columns(3)
    if image is not None:
        with left:
            st.write("Исходное изображение")
            st.image(image, use_column_width=True)

        with st.spinner("Восстановление геометрии..."):
            resp = requests.post(host, files={"file": image}, timeout=60)
            if resp.status_code != 200:
                st.error(f"Ошибка при отправке запроса: {resp.status_code}, {resp.text}")
                return
        res_image = resp.content
        res_text = resp.headers.get("X-Text")

        with middle:
            st.write("Результат восстановления геометрии")
            st.image(res_image, use_column_width=True)
        with right:
            st.write("Результат распознавания номера")
            st.write(f"**{res_text}**")


if __name__ == "__main__":
    main()
