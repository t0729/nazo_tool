import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import csv

clicked_points = []
highlighted_index = None
scale = 1.0
min_scale = 0.2
max_scale = 5.0
offset_x = 0
offset_y = 0
drag_start = None
is_drawing = False

def on_mouse_down(event):
    global is_drawing
    if move_mode.get() and highlighted_index is not None:
        drag_start = (event.x, event.y)
    else:
        is_drawing = True
        on_click(event)

def on_mouse_up(event):
    global is_drawing, drag_start
    is_drawing = False
    drag_start = None

def on_mouse_drag(event):
    global offset_x, offset_y, drag_start
    if move_mode.get() and highlighted_index is not None and drag_start:
        dx = int((event.x - drag_start[0]) / scale)
        dy = int((event.y - drag_start[1]) / scale)
        x, y = clicked_points[highlighted_index]
        clicked_points[highlighted_index] = (x + dx, y + dy)
        listbox.delete(highlighted_index)
        listbox.insert(highlighted_index, f"{highlighted_index+1}: ({x+dx}, {y+dy})")
        listbox.select_set(highlighted_index)
        drag_start = (event.x, event.y)
        draw_markers()
    elif is_drawing:
        on_click(event)

def on_click(event):
    global offset_x, offset_y
    x = int((event.x - offset_x) / scale)
    y = int((event.y - offset_y) / scale)
    clicked_points.append((x, y))
    listbox.insert(tk.END, f"{len(clicked_points)}: ({x}, {y})")
    listbox.select_clear(0, tk.END)
    listbox.select_set(len(clicked_points)-1)
    listbox.event_generate("<<ListboxSelect>>")

def on_select(event):
    global highlighted_index
    selection = listbox.curselection()
    if selection:
        highlighted_index = selection[0]
        draw_markers()

def on_delete():
    global highlighted_index
    if highlighted_index is not None:
        clicked_points.pop(highlighted_index)
        listbox.delete(highlighted_index)
        if clicked_points:
            next_index = min(highlighted_index, len(clicked_points)-1)
            listbox.select_set(next_index)
            listbox.event_generate("<<ListboxSelect>>")
        else:
            highlighted_index = None
            draw_markers()

def on_finish():
    with open("list.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y"])
        writer.writerows(clicked_points)
    print(f"\n✅ {len(clicked_points)} 点の座標を list.csv に保存しました。")
    root.quit()

def draw_markers():
    canvas.delete("MARK")
    for i, (x, y) in enumerate(clicked_points):
        rx = int(x * scale) + offset_x
        ry = int(y * scale) + offset_y
        color = "white" if i == highlighted_index else "red"
        canvas.create_oval(rx-4, ry-4, rx+4, ry+4, fill=color, outline="", tags="MARK")

def redraw(full=False):
    if full:
        canvas.delete("IMG")
        resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        global tk_img
        tk_img = ImageTk.PhotoImage(resized)
        canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=tk_img, tags="IMG")
    draw_markers()

def on_mousewheel(event):
    global scale, offset_x, offset_y
    old_scale = scale
    if event.delta > 0:
        scale = min(scale * 1.1, max_scale)
    else:
        scale = max(scale / 1.1, min_scale)

    mouse_x, mouse_y = event.x, event.y
    offset_x = int(mouse_x - (mouse_x - offset_x) * (scale / old_scale))
    offset_y = int(mouse_y - (mouse_y - offset_y) * (scale / old_scale))
    redraw(full=True)

def on_drag_start(event):
    global drag_start
    drag_start = (event.x, event.y)

def on_drag_move(event):
    global offset_x, offset_y, drag_start
    if drag_start:
        dx = event.x - drag_start[0]
        dy = event.y - drag_start[1]
        offset_x += dx
        offset_y += dy
        drag_start = (event.x, event.y)
        redraw(full=True)

# 画像選択
image_path = filedialog.askopenfilename(title="画像を選択", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
if not image_path:
    print("画像が選択されませんでした。終了します。")
    exit()

# GUI構築
root = tk.Tk()
root.title("座標記録ツール（描画・移動・ズーム対応）")

move_mode = tk.BooleanVar(value=False)
frame_left = tk.Frame(root)
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

listbox = tk.Listbox(frame_left, width=20)
listbox.pack(fill=tk.BOTH, expand=True)
listbox.bind("<<ListboxSelect>>", on_select)

tk.Checkbutton(frame_left, text="移動モード", variable=move_mode).pack(pady=5)
tk.Button(frame_left, text="削除", command=on_delete).pack(pady=5)
tk.Button(frame_left, text="完了", command=on_finish).pack(pady=5)

frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

img = Image.open(image_path)
tk_img = ImageTk.PhotoImage(img)

canvas = tk.Canvas(frame_right, width=img.width, height=img.height)
canvas.pack()
canvas.create_image(0, 0, anchor=tk.NW, image=tk_img, tags="IMG")

canvas.bind("<ButtonPress-1>", on_mouse_down)
canvas.bind("<B1-Motion>", on_mouse_drag)
canvas.bind("<ButtonRelease-1>", on_mouse_up)
canvas.bind("<MouseWheel>", on_mousewheel)
canvas.bind("<Button-4>", lambda e: on_mousewheel(type("Event", (), {"delta": 120})))
canvas.bind("<Button-5>", lambda e: on_mousewheel(type("Event", (), {"delta": -120})))
canvas.bind("<ButtonPress-3>", on_drag_start)
canvas.bind("<B3-Motion>", on_drag_move)

root.mainloop()
