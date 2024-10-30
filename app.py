import hashlib
from io import BytesIO
import os
import pickle

from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(
    page_title="PDF Editor",
    layout="wide",
)

def merge_pdfs(pdf_list, merge_order):
    pdf_writer = PdfWriter()
    
    for idx in merge_order:
        pdf_file = pdf_list[idx]
        pdf_reader = PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])

    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def rotate_pdf(pdf_file, rotation_angle, selected_pages):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()

    for page_num, page in enumerate(pdf_reader.pages):
        if page_num in selected_pages:
            page.rotate(rotation_angle)
        pdf_writer.add_page(page)
    
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def reorder_pages(pdf_file, selected_pages, target_page):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()

    all_pages = list(range(len(pdf_reader.pages)))
    
    for page in sorted(selected_pages, reverse=True):
        all_pages.pop(page)

    insert_index = target_page if target_page == 0 else all_pages.index(target_page - 1) + 1
    for page in selected_pages:
        all_pages.insert(insert_index, page)
        insert_index += 1

    for page_num in all_pages:
        pdf_writer.add_page(pdf_reader.pages[page_num])
    
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def resize_and_add_black_border(img, target_width, target_height):
    original_width, original_height = img.size

    aspect_ratio = original_width / original_height

    if target_width / target_height > aspect_ratio:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    else:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)

    img = img.resize((new_width, new_height))

    new_image = Image.new("RGB", (target_width, target_height), (0, 0, 0))
    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2
    new_image.paste(img, (offset_x, offset_y))

    return new_image

def delete_pages(pdf_file, selected_pages):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()

    for page_num, page in enumerate(pdf_reader.pages):
        if page_num not in selected_pages:
            pdf_writer.add_page(page)
    
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def extract_pages(pdf_file, selected_pages):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()

    for page_num in selected_pages:
        pdf_writer.add_page(pdf_reader.pages[page_num])
    
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def calculate_object_hash(obj):
    obj_bytes = pickle.dumps(obj)
    return hashlib.md5(obj_bytes).hexdigest()


option = st.sidebar.radio(
    "Select an action",
    options=["Merge PDFs", "Rotate Pages", "Reorder Pages", "Delete or Extract Pages"]
)

with st.sidebar.expander("Settings", expanded=False):
    cols_per_row = st.selectbox("Number of columns per row", options=[1, 2, 3, 4, 5, 6], index=2)

    image_size = st.slider("Thumbnail size (width and height)", min_value=100, max_value=500, value=200)


st.title("PDF Editor")

st.header(option)

if option == "Merge PDFs":
    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if "file_hash_m" in st.session_state and st.session_state.file_hash_m != calculate_object_hash(uploaded_files):
            del st.session_state.pdf_images_
            if "merge_order" in st.session_state:
                del st.session_state.merge_order

        st.session_state.file_hash_m = calculate_object_hash(uploaded_files)

        st.session_state.pdf_images_ = []
        file_names = [file.name for file in uploaded_files]

        for file in uploaded_files:
            st.session_state.pdf_images_.append(convert_from_bytes(file.read(), first_page=0, last_page=1))

        if "merge_order" not in st.session_state:
            st.session_state.merge_order = []

        if any(m + 1 > len(st.session_state.pdf_images_) for m in st.session_state.merge_order):
            st.session_state.merge_order = []

        if st.button("Select All"):
            st.session_state.merge_order = list(range(len(st.session_state.pdf_images_)))

        if st.button("Reset Selection"):
            st.session_state.merge_order = []

        st.write("Click on the PDF number to select the merge order.")

        cols = st.columns(cols_per_row)

        for i, (pdf_image, file_name) in enumerate(zip(st.session_state.pdf_images_, file_names)):
            col = cols[i % cols_per_row]
            with col:
                if st.button(f"PDF {i+1}", key=f"PDF_{i+1}"):
                    if i in st.session_state.merge_order:
                        st.session_state.merge_order.remove(i)
                    else:
                        st.session_state.merge_order.append(i)

                tmp_image = resize_and_add_black_border(pdf_image[0], image_size, image_size)
                st.image(tmp_image, caption=file_name, width=image_size)

        if st.session_state.merge_order:
            st.write(f"Selected merge order: {[i + 1 for i in st.session_state.merge_order]}")
        else:
            st.write("No PDF selected for merging.")

        if st.session_state.merge_order:
            merged_pdfs = merge_pdfs(uploaded_files, st.session_state.merge_order)
            st.download_button(
                label="Download Merged PDF",
                data=merged_pdfs,
                file_name="merged_pdfs.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Please upload PDF files to merge.")

elif option == "Rotate Pages":
    uploaded_file = st.file_uploader("Upload a PDF file to rotate", type=["pdf"])

    if uploaded_file:
        if "file_hash_ro" in st.session_state and st.session_state.file_hash_ro != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images
            del st.session_state.selected_pages
            if "rotated_pdf" in st.session_state:
                del st.session_state.rotated_pdf

        st.session_state.file_hash_ro = calculate_object_hash(uploaded_file)

        if "pdf_images" not in st.session_state or st.session_state.pdf_images is None:
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())

        if "selected_pages" not in st.session_state:
            st.session_state.selected_pages = []
        
        if st.button("Reset to Original"):
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())
            st.session_state.selected_pages = []
            if "updated_pdf" in st.session_state:
                del st.session_state.updated_pdf
            st.success("PDF has been reset to the original upload state!")
            st.rerun()

        if st.button("Select All"):
            st.session_state.selected_pages = list(range(len(st.session_state.pdf_images)))

        if st.button("Reset Selection"):
            st.session_state.selected_pages = []

        st.write("Click on a thumbnail to select/deselect pages for rotation:")

        cols = st.columns(cols_per_row)

        for i, image in enumerate(st.session_state.pdf_images):
            col = cols[i % cols_per_row]
            with col:
                if st.button(f"Page {i+1}", key=f"page_{i+1}"):
                    if i in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(i)
                    else:
                        st.session_state.selected_pages.append(i)

                tmp_image = resize_and_add_black_border(image, image_size, image_size)
                st.image(tmp_image, caption=f"Page {i+1}", width=image_size)

        if st.session_state.selected_pages:
            st.write(f"Selected pages: {[i + 1 for i in st.session_state.selected_pages]}")
        else:
            st.write("No pages selected.")

        rotation_angle = st.selectbox("Choose rotation angle", (90, 180, 270))

        if st.button("Rotate"):
            if st.session_state.selected_pages:
                if "rotated_pdf" in st.session_state:
                    st.session_state.rotated_pdf = rotate_pdf(st.session_state.rotated_pdf, rotation_angle, st.session_state.selected_pages)
                else:
                    st.session_state.rotated_pdf = rotate_pdf(uploaded_file, rotation_angle, st.session_state.selected_pages)
                st.success("Selected pages rotated successfully!")

                st.session_state.pdf_images = convert_from_bytes(st.session_state.rotated_pdf.read())
                st.session_state.selected_pages = []
                st.rerun()
            else:
                st.error("Please select at least one page to rotate.")
        
        if "rotated_pdf" in st.session_state:
            base_name, _ = os.path.splitext(uploaded_file.name)
            st.download_button(
                label="Download Rotated PDF",
                data=st.session_state.rotated_pdf,
                file_name=base_name + "_rotated.pdf",
                mime="application/pdf"
            )

    else:
        st.info("Please upload a PDF file to see available pages.")

elif option == "Reorder Pages":
    uploaded_file = st.file_uploader("Upload a PDF file to reorder", type=["pdf"])

    if uploaded_file:
        if "file_hash_re" in st.session_state and st.session_state.file_hash_re != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images
            del st.session_state.selected_pages
            if "reordered_pdf" in st.session_state:
                del st.session_state.reordered_pdf

        st.session_state.file_hash_re = calculate_object_hash(uploaded_file)

        if "pdf_images" not in st.session_state or st.session_state.pdf_images is None:
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())

        if "selected_pages" not in st.session_state:
            st.session_state.selected_pages = []

        if st.button("Reset to Original"):
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())
            st.session_state.selected_pages = []
            if "updated_pdf" in st.session_state:
                del st.session_state.updated_pdf
            st.success("PDF has been reset to the original upload state!")
            st.rerun()

        if st.button("Reset Selection"):
            st.session_state.selected_pages = []

        st.write("Click on a thumbnail to select/deselect pages for reordering:")

        cols = st.columns(cols_per_row)

        for i, image in enumerate(st.session_state.pdf_images):
            col = cols[i % cols_per_row]
            with col:
                if st.button(f"Page {i+1}", key=f"page_{i+1}"):
                    if i in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(i)
                    else:
                        st.session_state.selected_pages.append(i)

                tmp_image = resize_and_add_black_border(image, image_size, image_size)
                st.image(tmp_image, caption=f"Page {i+1}", width=image_size)

        if st.session_state.selected_pages:
            st.write(f"Selected pages: {[i + 1 for i in st.session_state.selected_pages]}")
        else:
            st.write("No pages selected.")

        tmp_target_page = [i for i in range(len(st.session_state.pdf_images))]
        tmp_target_page = [item for item in tmp_target_page if item not in st.session_state.selected_pages]
        tmp_target_page = [0] + [i + 1 for i in tmp_target_page]
        target_page = st.selectbox("Select the page after which the selected pages should be moved",
                                   options=tmp_target_page)

        if st.button("Reorder"):
            if st.session_state.selected_pages:
                if "reordered_pdf" in st.session_state:
                    st.session_state.reordered_pdf = reorder_pages(st.session_state.reordered_pdf, st.session_state.selected_pages, target_page)
                else:
                    st.session_state.reordered_pdf = reorder_pages(uploaded_file, st.session_state.selected_pages, target_page)
                st.success("Pages reordered successfully!")

                st.session_state.pdf_images = convert_from_bytes(st.session_state.reordered_pdf.read())
                st.session_state.selected_pages = []
                st.rerun()
            else:
                st.error("Please select at least one page to reorder.")

        if "reordered_pdf" in st.session_state:
            base_name, _ = os.path.splitext(uploaded_file.name)
            st.download_button(
                label="Download Reordered PDF",
                data=st.session_state.reordered_pdf,
                file_name=base_name + "_reordered.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Please upload a PDF file to reorder.")
elif option == "Delete or Extract Pages":
    uploaded_file = st.file_uploader("Upload a PDF file to delete or extract pages", type=["pdf"])

    if uploaded_file:
        if "file_hash_del_ext" in st.session_state and st.session_state.file_hash_del_ext != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images
            del st.session_state.selected_pages
            if "updated_pdf" in st.session_state:
                del st.session_state.updated_pdf

        st.session_state.file_hash_del_ext = calculate_object_hash(uploaded_file)

        if "pdf_images" not in st.session_state or st.session_state.pdf_images is None:
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())

        if "selected_pages" not in st.session_state:
            st.session_state.selected_pages = []

        if st.button("Reset to Original"):
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())
            st.session_state.selected_pages = []
            if "updated_pdf" in st.session_state:
                del st.session_state.updated_pdf
            st.success("PDF has been reset to the original upload state!")
            st.rerun()

        if st.button("Reset Selection"):
            st.session_state.selected_pages = []

        st.write("Click on a thumbnail to select/deselect pages to delete or extract:")

        cols = st.columns(cols_per_row)

        for i, image in enumerate(st.session_state.pdf_images):
            col = cols[i % cols_per_row]
            with col:
                if st.button(f"Page {i+1}", key=f"page_del_ext_{i+1}"):
                    if i in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(i)
                    else:
                        st.session_state.selected_pages.append(i)

                tmp_image = resize_and_add_black_border(image, image_size, image_size)
                st.image(tmp_image, caption=f"Page {i+1}", width=image_size)

        if st.session_state.selected_pages:
            st.write(f"Selected pages: {[i + 1 for i in st.session_state.selected_pages]}")
        else:
            st.write("No pages selected.")

        if len(st.session_state.pdf_images) == 1:
            action = st.radio("Choose action", ("Extract Selected Pages (Cannot delete. There is only one page.)"))
        else:
            action = st.radio("Choose action", ("Delete Selected Pages", "Extract Selected Pages"))

        if st.button("Apply"):
            if st.session_state.selected_pages:
                if action == "Delete Selected Pages":
                    st.session_state.updated_pdf = delete_pages(uploaded_file, st.session_state.selected_pages)
                elif action == "Extract Selected Pages":
                    st.session_state.updated_pdf = extract_pages(uploaded_file, st.session_state.selected_pages)
                
                st.success(f"Pages {action.lower()} successfully!")

                st.session_state.pdf_images = convert_from_bytes(st.session_state.updated_pdf.read())
                st.session_state.selected_pages = []
                st.rerun()
            else:
                st.error("Please select at least one page.")

        if "updated_pdf" in st.session_state:
            base_name, _ = os.path.splitext(uploaded_file.name)
            st.download_button(
                label=f"Download {action.split()[0]}d PDF",
                data=st.session_state.updated_pdf,
                file_name=base_name + f"_{action.split()[0].lower()}d.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Please upload a PDF file to delete or extract pages.")
