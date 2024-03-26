import os
import sys
import cv2
from easydict import EasyDict
import xml.etree.ElementTree as ET
from PIL import Image



test_screen = "C:/Users/yznzh/OneDrive/文档/Agent/AAA_xiaomi_13/settings_1/settings_1.step_3"
test_screen_png = test_screen + ".png"
test_screen_xml = test_screen + ".xml"
test_screen_activities = test_screen + ".activities.log"
output_dir = "./test_output_step_3"
os.makedirs(output_dir, exist_ok=True)

image = Image.open(test_screen_png)

screen_w = image.width
screen_h = image.height


def get_id_from_element(elem):
    bounds = elem.attrib["bounds"][1:-1].split("][")
    x1, y1 = map(int, bounds[0].split(","))
    x2, y2 = map(int, bounds[1].split(","))
    elem_w, elem_h = x2 - x1, y2 - y1
    if "resource-id" in elem.attrib and elem.attrib["resource-id"]:
        elem_id = elem.attrib["resource-id"].replace(":", ".").replace("/", "_")
    else:
        elem_id = f"{elem.attrib['class']}_{elem_w}_{elem_h}"
    if "content-desc" in elem.attrib and elem.attrib["content-desc"] and len(elem.attrib["content-desc"]) < 20:
        content_desc = elem.attrib['content-desc'].replace("/", "_").replace(" ", "").replace(":", "_")
        elem_id += f"_{content_desc}"
    return elem_id

def item_in(item1, item2):
    if item1.x1 > item2.x1 and \
        item1.x2 < item2.x2 and \
        item1.y1 > item2.y1 and \
        item1.y2 < item2.y2:
        return True
    return False

def traverse_tree(xml_path, true_attrib, add_index=True, min_w=10, min_h=10, 
                screen_w=screen_w, screen_h=screen_h,
                size_ratio_lower_limit=None,
                size_ratio_upper_limit=None,
                filter_inner_item=False,
                filter_outer_item=False):
    path = []
    elem_list = []
    if isinstance(true_attrib, str):
        true_attrib = [true_attrib,]
    
    for event, elem in ET.iterparse(xml_path, ['start', 'end']):
        if event == 'start':
            path.append(elem)
            
            hit = False
            for a in true_attrib:
                if a in elem.attrib and elem.attrib[a] == "true":
                    hit = True
                    break

            if hit:
                parent_prefix = ""
                if len(path) > 1:
                    parent_prefix = get_id_from_element(path[-2])
                bounds = elem.attrib["bounds"][1:-1].split("][")
                x1, y1 = map(int, bounds[0].split(","))
                x2, y2 = map(int, bounds[1].split(","))
                
                if x2 - x1 < min_w or y2 - y1 < min_h:
                    continue

                size_ratio = float((x2 - x1) * (y2 - y1)) / float(screen_w * screen_h)
                if size_ratio_upper_limit is not None and size_ratio > size_ratio_upper_limit:
                    continue
                if size_ratio_lower_limit is not None and size_ratio < size_ratio_lower_limit:
                    continue

                elem_id = get_id_from_element(elem)
                if parent_prefix:
                    elem_id = parent_prefix + "_" + elem_id
                if add_index:
                    elem_id += f"_{elem.attrib['index']}"

                elem_list.append(EasyDict({
                    "id" : elem_id, 
                    "bounds" : ((x1, y1), (x2, y2)), 
                    "x1" : x1,
                    "y1" : y1,
                    "x2" : x2,
                    "y2" : y2,
                    "cx" : (x1 + x2) // 2,
                    "cy" : (y1 + y2) // 2,
                    "attrib" : elem.attrib,
                }))

        if event == 'end':
            path.pop()
    
    if filter_inner_item:
        # 对于相互包围的元素，仅保留最外围的元素
        filtered_item_list = []
        for item in elem_list:
            filter = False
            for item2 in elem_list:
                if item_in(item, item2):
                    filter = True
                    break
            if not filter:
                filtered_item_list.append(item)
        elem_list = filtered_item_list

    if filter_outer_item:
        # 对于相互包围的元素，仅保留最内围的元素
        filtered_item_list = []
        for item in elem_list:
            filter = False
            for item2 in elem_list:
                if item_in(item2, item):
                    filter = True
                    break
            if not filter:
                filtered_item_list.append(item)
        elem_list = filtered_item_list

    return elem_list




hit_list = traverse_tree(test_screen_xml, ["focusable", "clickable"], size_ratio_upper_limit=0.15)

for item in hit_list:
    # cropped_image = image.crop((item.x1, item.y1, item.x2, item.y2))
    # item_id = "hit_" + item.id.replace("\\", "_").replace("/", "_") + ".png"
    print(item)
    # cropped_image.save(os.path.join(output_dir, item_id))


scroller_list = traverse_tree(test_screen_xml, "scrollable", filter_inner_item=True)

print("scroller_list : ")
for item in scroller_list:
    print(item)




# focusable_list = []
# traverse_tree(test_screen_xml, focusable_list, "focusable")

# for item in focusable_list:
#     cropped_image = image.crop((item.x1, item.y1, item.x2, item.y2))
#     item_id = "focusable_" + item.id.replace("\\", "_").replace("/", "_") + ".png"
#     cropped_image.save(os.path.join(output_dir, item_id))

# clickable_list = []
# traverse_tree(test_screen_xml, clickable_list, "clickable")

# for item in clickable_list:
#     cropped_image = image.crop((item.x1, item.y1, item.x2, item.y2))
#     item_id = "clickable_" + item.id.replace("\\", "_").replace("/", "_") + ".png"
#     cropped_image.save(os.path.join(output_dir, item_id))


# focused_list = []
# traverse_tree(test_screen_xml, focused_list, "focused")

# for item in focused_list:
#     cropped_image = image.crop((item.x1, item.y1, item.x2, item.y2))
#     item_id = "focused_" + item.id.replace("\\", "_").replace("/", "_") + ".png"
#     cropped_image.save(os.path.join(output_dir, item_id))

# scrollable_list = []
# traverse_tree(test_screen_xml, scrollable_list, "scrollable")

# for item in scrollable_list:
#     cropped_image = image.crop((item.x1, item.y1, item.x2, item.y2))
#     item_id = "scrollable_" + item.id.replace("\\", "_").replace("/", "_") + ".png"
#     cropped_image.save(os.path.join(output_dir, item_id))


