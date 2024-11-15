import json
import cv2
import random
import streamlit as st
from PIL import Image
import numpy as np

# 고유 색상 할당 함수
def get_unique_color(existing_colors):
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    while color in existing_colors:
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return color

# JSON 데이터에서 바운딩 박스를 추출하는 함수
def extract_bboxes(json_data):
    bboxes = []
    for annotation in json_data.get('annotations', []):
        for result in annotation.get('result', []):
            from_name = result.get('from_name')
            if from_name in ['elements', 'class', 'meta']:
                x = result['value']['x']
                y = result['value']['y']
                w = result['value']['width']
                h = result['value']['height']
                labels = result['value']['rectanglelabels']
                parent_id = result.get('parent_id', None)
                group_type = None
                if 'group_id' in result:
                    group_type = 'Parent Group'
                elif 'a_group_id' in result:
                    group_type = 'a group'
                elif 'element_count' in result:
                    group_type = 'Subgroup'
                bboxes.append((x, y, w, h, group_type, labels, parent_id))
    return bboxes

# --1 번 옵션: parent_id에 따라 색상 지정
def visualize_bbox_option1(image, bboxes):
    parent_color_map = {}
    
    for bbox in bboxes:
        x, y, w, h, group_type, labels, parent_id = bbox
        color = parent_color_map.get(parent_id, get_unique_color(parent_color_map.values()))
        parent_color_map[parent_id] = color

        cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)
        if 'Title' in labels:
            cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), (10, 10, 10), 2)
            cv2.putText(image, 'Title', (int(x), int(y) - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (10, 10, 10), 2)
    
    return image

# --2 번 옵션: 그룹별 색상 지정
def visualize_bbox_option2(image, bboxes):
    image_height, image_width = image.shape[:2]

    for bbox in bboxes:
        x, y, w, h, group_type, labels, _ = bbox

        x = int(x * image_width / 100) if x < 1 else int(x)
        y = int(y * image_height / 100) if y < 1 else int(y)
        w = int(w * image_width / 100) if w < 1 else int(w)
        h = int(h * image_height / 100) if h < 1 else int(h)

        if 'a group' in labels:
            color = (0, 0, 255)
            label = 'a group'
        elif 'Parent Group' in labels:
            color = (0, 255, 0)
            label = 'Parent Group'
        elif 'Subgroup' in labels:
            color = (255, 0, 0)
            label = 'Subgroup'
        else:
            color = (255, 255, 255)
            label = 'None'

        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        if 'Title' in labels and ('Subgroup' not in labels and 'Parent Group' not in labels and 'a group' not in labels):
            cv2.rectangle(image, (x, y), (x + w, y + h), (10, 10, 10), 4)
            cv2.putText(image, 'Title', (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (10, 10, 10), 4)

    return image

# --3 번 옵션: pattern_id에 따라 색상 지정
def visualize_bbox_option3(image, bboxes):
    image_height, image_width = image.shape[:2]
    pattern_color_map = {}

    subgroup_bboxes = [bbox for bbox in bboxes if bbox[4] == 'Subgroup']
    pattern_groups = {}

    for bbox in subgroup_bboxes:
        _, _, _, _, _, _, pattern_id = bbox
        if pattern_id not in pattern_groups:
            pattern_groups[pattern_id] = []
        pattern_groups[pattern_id].append(bbox)

    for pattern_id, bboxes in pattern_groups.items():
        if pattern_id not in pattern_color_map:
            pattern_color_map[pattern_id] = get_unique_color(pattern_color_map.values())
        
        color = pattern_color_map[pattern_id]

        for bbox in bboxes:
            x, y, w, h, group_type, labels, _ = bbox

            x = int(x * image_width / 100) if x < 1 else int(x)
            y = int(y * image_height / 100) if y < 1 else int(y)
            w = int(w * image_width / 100) if w < 1 else int(w)
            h = int(h * image_height / 100) if h < 1 else int(h)

            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            cv2.putText(image, ','.join(labels), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            if 'Title' in labels:
                cv2.rectangle(image, (x, y), (x + w, y + h), (10, 10, 10), 2)
                cv2.putText(image, 'Title', (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (10, 10, 10), 2)

    return image

# Streamlit 애플리케이션 함수
def main():
    st.title("Bounding Box Visualization")

    json_files = st.file_uploader("Upload JSON files", type="json", accept_multiple_files=True)
    image_files = st.file_uploader("Upload Image files", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    option = st.selectbox("Choose an option", ("--1", "--2", "--3"))

    if json_files and image_files:
        for json_file, image_file in zip(json_files, image_files):
            json_data = json.load(json_file)
            bboxes = extract_bboxes(json_data)

            image = Image.open(image_file)
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            if option == '--1':
                st.write(f"Visualizing with Option 1 for {image_file.name}")
                result_image = visualize_bbox_option1(image.copy(), bboxes)

            elif option == '--2':
                st.write(f"Visualizing with Option 2 for {image_file.name}")
                result_image = visualize_bbox_option2(image.copy(), bboxes)

            elif option == '--3':
                st.write(f"Visualizing with Option 3 for {image_file.name}")
                result_image = visualize_bbox_option3(image.copy(), bboxes)

            st.image(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB), channels="RGB", caption=image_file.name)

# 스트림릿 앱 실행
if __name__ == "__main__":
    main()
