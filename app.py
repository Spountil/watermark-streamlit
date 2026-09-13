
import os
import io
import zipfile
import gc
import streamlit as st
from google.cloud import storage
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
FILE_NAME = os.getenv("FILE_NAME")

@st.cache_data
def get_watermark(
    project_id: str,
    bucket_name: str,
    file_name: str
) -> bytes:
    """" 
    Downaload the watermark image stored in a Google Storage bucket
    """

    client = storage.Client(project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    watermark_bytes = blob.download_as_bytes()

    return watermark_bytes


watermark_bytes = get_watermark(
    project_id=PROJECT_ID,
    bucket_name=BUCKET_NAME,
    file_name=FILE_NAME
)
watermark = Image.open(io.BytesIO(watermark_bytes)).convert("RGBA")
    
st.title("Bienvenue!")

resize_value = st.number_input(
    label="Choisir la taille du logo en pourcentage de l'image",
    min_value=0.0,
    max_value=1.0,
    value=0.4,
    step=0.05,
)

opacity_percentage = st.number_input(
    label="Choisir l'opacité du logo",
    min_value=0.0,
    max_value=1.0,
    value=0.4,
    step=0.05,
)

watermark_color = st.radio(
    label="Couleur du logo",
    options=["Blanc", "Noir"],
    horizontal=True
)

max_size = (1920, 1080)

files = st.file_uploader(
    label="Ajouter les photos ici",
    type="image/*",
    accept_multiple_files=True,
)

if files:

    if st.button("Traiter les photos"):

        progress_bar = st.progress(
            0,
            text="Préparation du traitement..."
        )

        total_files = len(files)
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, file in enumerate(files):
                if file is None:
                    continue

                percent_complete = (i + 1) / total_files
                progress_bar.progress(
                    percent_complete,
                    text=f"Traitement de {file.name} ({i+1}/{total_files})"
                )

                img = Image.open(file)
                img.thumbnail(max_size)

                img_width, img_height = img.size
                watermark_width, watermark_height = watermark.size
                new_watermark_width = int(img_width * resize_value)
                ratio = new_watermark_width / watermark_width
                new_watermark_height = int(watermark_height * ratio)

                scaled_watermark = watermark.resize(
                    (new_watermark_width, new_watermark_height),
                    Image.Resampling.LANCZOS
                )

                paste_x = (img_width - new_watermark_width) // 2
                paste_y = (img_height - new_watermark_height) // 2

                r, g, b, a = scaled_watermark.split()
                a = a.point(lambda p: int(p * opacity_percentage))
                scaled_watermark.putalpha(a)

                if watermark_color == "Blanc":
                    new_r = r.point(lambda _: 255)
                    new_g = g.point(lambda _: 255)
                    new_b = b.point(lambda _: 255)
                else:
                    new_r = r.point(lambda _: 0)
                    new_g = g.point(lambda _: 0)
                    new_b = b.point(lambda _: 0)

                scaled_watermark = Image.merge("RGBA", (new_r, new_g, new_b, a))

                img.paste(scaled_watermark, (paste_x, paste_y), mask=scaled_watermark)

                img = img.convert("RGB")
                temp_img_buffer = io.BytesIO()
                img.save(temp_img_buffer, format="JPEG")

                original_name = file.name
                name_without_ext = os.path.splitext(original_name)[0]
                new_filename = f"{name_without_ext}.jpg"

                zip_file.writestr(new_filename, temp_img_buffer.getvalue())

                del img
                del scaled_watermark
                del temp_img_buffer

                gc.collect()

        progress_bar.empty()

        st.session_state["processed_zip"] = zip_buffer.getvalue()
        st.success("Traitement terminé ! Vous pouvez télécharger les photos")

    if "processed_zip" in st.session_state:
        st.download_button(
            label="📥 Télécharger les photos",
            data=st.session_state["processed_zip"],
            file_name="photos_watermarked.zip",
            mime="application/zip"
        )




            