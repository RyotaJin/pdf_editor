import hashlib
import pickle
import streamlit as st
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image
import os

# 処理選択
st.title("PDF Editor")

# サイドバーで処理を選択
option = st.sidebar.radio(
    "Select an action",
    options=["Merge PDFs", "Rotate Pages", "Reorder Pages"]
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
    
    # 結果をBytesIOに保存
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def reorder_pages(pdf_file, selected_pages, target_page):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()

    # ページを新しい順序で並べるためのリストを作成
    all_pages = list(range(len(pdf_reader.pages)))
    
    # 移動対象のページをリストから除外
    for page in sorted(selected_pages, reverse=True):
        all_pages.pop(page)

    # ターゲットページの位置を確認し、その後ろに選択したページを挿入
    # insert_index = all_pages.index(target_page) + 1
    insert_index = target_page if target_page == 0 else all_pages.index(target_page - 1) + 1
    for page in selected_pages:
        all_pages.insert(insert_index, page)
        insert_index += 1

    # 新しい順序でPDFを書き込み
    for page_num in all_pages:
        pdf_writer.add_page(pdf_reader.pages[page_num])
    
    # 結果をBytesIOに保存
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

def get_new_width(original_size, max_width, max_height):
    original_width = original_size[0]
    original_height = original_size[1]
    aspect_ratio = original_width / original_height
    
    # 新しいサイズを計算
    if original_width > original_height:
        new_width = min(max_width, original_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(max_height, original_height)
        new_width = int(new_height * aspect_ratio)
    return new_width

def resize_and_add_black_border(img, target_width, target_height):
    # 元のサイズを取得
    original_width, original_height = img.size

    # アスペクト比を計算
    aspect_ratio = original_width / original_height

    # 新しいサイズを計算
    if target_width / target_height > aspect_ratio:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    else:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)

    # リサイズ
    img = img.resize((new_width, new_height))

    # 黒い余白の追加
    new_image = Image.new("RGB", (target_width, target_height), (0, 0, 0))
    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2
    new_image.paste(img, (offset_x, offset_y))

    return new_image

def calculate_object_hash(obj):
    # オブジェクトをバイト列にシリアライズ化する
    obj_bytes = pickle.dumps(obj)
    # ハッシュ化
    return hashlib.md5(obj_bytes).hexdigest()


cols_per_row = 3  # 1行に並べるサムネイルの数
width_ = 200
height_ = 200

# Merge PDFs UI
if option == "Merge PDFs":
    st.header("Merge PDFs")
    
    uploaded_file = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_file:
        if "file_hash_m" in st.session_state and st.session_state.file_hash_m != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images_
            del st.session_state.merge_order

        st.session_state.file_hash_m = calculate_object_hash(uploaded_file)

        st.session_state.pdf_images_ = []
        for file in uploaded_file:
            st.session_state.pdf_images_.append(convert_from_bytes(file.read(), first_page=0, last_page=1))

        # 選択されたページのインデックスをセッションステートで保持
        if "merge_order" not in st.session_state:
            st.session_state.merge_order = []

        if any(m + 1 > len(st.session_state.pdf_images_) for m in st.session_state.merge_order):
            st.session_state.merge_order = []

        st.write("Click on the PDF number to select the merge order.")

        # サムネイルの表示と操作
        cols = st.columns(cols_per_row)

        for i, (pdf_image) in enumerate(st.session_state.pdf_images_):
            col = cols[i % cols_per_row]
            with col:
                # サムネイル表示
                if st.button(f"PDF {i+1}", key=f"PDF_{i+1}"):
                    # 順番を選択
                    if i in st.session_state.merge_order:
                        st.session_state.merge_order.remove(i)
                    else:
                        st.session_state.merge_order.append(i)

                # サムネイル画像を表示
                tmp_image = resize_and_add_black_border(pdf_image[0], width_, height_)
                # st.image(tmp_image[0], caption=f"Page {i+1}", width=width_)
                st.image(tmp_image, caption=f"PDF {i+1}", width=200)

        # 選択された順番を表示
        if st.session_state.merge_order:
            st.write(f"Selected merge order: {[i + 1 for i in st.session_state.merge_order]}")
        else:
            st.write("No PDF selected for merging.")

        # マージボタン
        if st.session_state.merge_order:
            merged_pdfs = merge_pdfs(uploaded_file, st.session_state.merge_order)
            st.download_button(
                label="Download Merged PDF",
                data=merged_pdfs,
                file_name="merged_pdfs.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Please upload PDF files to merge.")

# Rotate PDF UI
elif option == "Rotate Pages":
    st.header("Rotate Pages")
    uploaded_file = st.file_uploader("Upload a PDF file to rotate", type=["pdf"])

    if uploaded_file:
        if "file_hash_ro" in st.session_state and st.session_state.file_hash_ro != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images
            del st.session_state.selected_pages
            if "rotated_pdf" in st.session_state:
                del st.session_state.rotated_pdf

        st.session_state.file_hash_ro = calculate_object_hash(uploaded_file)

        # PDFを画像に変換してサムネイルを表示
        if "pdf_images" not in st.session_state or st.session_state.pdf_images is None:
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())

        # 選択されたページのインデックスをセッションステートで保持
        if "selected_pages" not in st.session_state:
            st.session_state.selected_pages = []
        
        st.write("Click on a thumbnail to select/deselect pages for rotation:")

        # 列を用いてサムネイルを横方向に並べる
        cols = st.columns(cols_per_row)

        for i, image in enumerate(st.session_state.pdf_images):
            col = cols[i % cols_per_row]
            with col:
                # サムネイル画像表示
                if st.button(f"Page {i+1}", key=f"page_{i+1}"):
                    # クリックでページを選択または解除
                    if i in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(i)
                    else:
                        st.session_state.selected_pages.append(i)

                # サムネイルの下にページ番号を表示
                tmp_image = resize_and_add_black_border(image, width_, height_)
                st.image(tmp_image, caption=f"Page {i+1}", width=width_)

        # 現在選択されているページを表示
        if st.session_state.selected_pages:
            st.write(f"Selected pages: {[i + 1 for i in st.session_state.selected_pages]}")
        else:
            st.write("No pages selected.")

        # 回転角度を選択
        rotation_angle = st.selectbox("Choose rotation angle", (90, 180, 270))

        if st.button("Rotate"):
            if st.session_state.selected_pages:
                if "rotated_pdf" in st.session_state:
                    st.session_state.rotated_pdf = rotate_pdf(st.session_state.rotated_pdf, rotation_angle, st.session_state.selected_pages)
                else:
                    st.session_state.rotated_pdf = rotate_pdf(uploaded_file, rotation_angle, st.session_state.selected_pages)
                st.success("Selected pages rotated successfully!")

                # サムネイルをアップデート（回転後のサムネイルを再生成）
                st.session_state.pdf_images = convert_from_bytes(st.session_state.rotated_pdf.read())
                st.session_state.selected_pages = []
                st.rerun()
            else:
                st.error("Please select at least one page to rotate.")
        
        if "rotated_pdf" in st.session_state:
            # ダウンロードボタン
            base_name, _ = os.path.splitext(uploaded_file.name)
            st.download_button(
                label="Download Rotated PDF",
                data=st.session_state.rotated_pdf,
                file_name=base_name + "_rotated.pdf",
                mime="application/pdf"
            )

    else:
        st.info("Please upload a PDF file to see available pages.")

# Reorder Pages UI
elif option == "Reorder Pages":
    st.header("Reorder Pages")
    uploaded_file = st.file_uploader("Upload a PDF file to reorder", type=["pdf"])

    if uploaded_file:
        if "file_hash_re" in st.session_state and st.session_state.file_hash_re != calculate_object_hash(uploaded_file):
            del st.session_state.pdf_images
            del st.session_state.selected_pages
            if "reordered_pdf" in st.session_state:
                del st.session_state.reordered_pdf

        st.session_state.file_hash_re = calculate_object_hash(uploaded_file)

        # PDFを画像に変換してサムネイルを表示
        if "pdf_images" not in st.session_state or st.session_state.pdf_images is None:
            st.session_state.pdf_images = convert_from_bytes(uploaded_file.read())

        # 選択されたページのインデックスをセッションステートで保持
        if "selected_pages" not in st.session_state:
            st.session_state.selected_pages = []

        st.write("Click on a thumbnail to select/deselect pages for reordering:")

        # サムネイルの表示
        cols = st.columns(cols_per_row)

        for i, image in enumerate(st.session_state.pdf_images):
            col = cols[i % cols_per_row]
            with col:
                # サムネイル画像表示
                if st.button(f"Page {i+1}", key=f"page_{i+1}"):
                    # クリックでページを選択または解除
                    if i in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(i)
                    else:
                        st.session_state.selected_pages.append(i)

                # サムネイルの下にページ番号を表示
                tmp_image = resize_and_add_black_border(image, width_, height_)
                st.image(tmp_image, caption=f"Page {i+1}", width=width_)

        # 現在選択されているページを表示
        if st.session_state.selected_pages:
            st.write(f"Selected pages: {[i + 1 for i in st.session_state.selected_pages]}")
        else:
            st.write("No pages selected.")

        # 移動先のページを選択
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

                # サムネイルをアップデート（回転後のサムネイルを再生成）
                st.session_state.pdf_images = convert_from_bytes(st.session_state.reordered_pdf.read())
                st.session_state.selected_pages = []
                st.rerun()
            else:
                st.error("Please select at least one page to reorder.")

        if "reordered_pdf" in st.session_state:
            base_name, _ = os.path.splitext(uploaded_file.name)
            # ダウンロードボタン
            st.download_button(
                label="Download Reordered PDF",
                data=st.session_state.reordered_pdf,
                file_name=base_name + "_reordered.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Please upload a PDF file to reorder.")
