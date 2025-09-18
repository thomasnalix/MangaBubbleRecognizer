import os
import tkinter as tk
from PIL import Image, ImageTk

IMAGES_DIR = os.path.join('data', 'images', 'train')
LABELS_DIR = os.path.join('data', 'labels', 'train')

os.makedirs(LABELS_DIR, exist_ok=True)

class BubbleAnnotator:
    def __init__(self, root, images):
        self.root = root
        self.images = images
        self.current_index = 120
        self.boxes = []
        self.box_objects = []  # Store canvas IDs and handles
        self.start_x = self.start_y = 0
        self.current_rect = None
        self.img_tk = None
        self.selected_box = None
        self.resize_handle = None
        self.current_class = 0  # Default class (0 = speech bubble, 1 = text)
        self.corner_size = 6  # Size of resize handles
        
        self.root.title("Manga Bubble Annotator")
        self.root.geometry("1200x800")
        
        info_frame = tk.Frame(root)
        info_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        self.status_label = tk.Label(info_frame, text="", font=("Arial", 10))
        self.status_label.pack(side="left")
        
        # Add class selector
        class_frame = tk.Frame(info_frame)
        class_frame.pack(side="left", padx=20)
        
        self.class_var = tk.IntVar(value=0)
        tk.Radiobutton(class_frame, text="Speech Bubble", variable=self.class_var, 
                      value=0, command=self.update_class).pack(side="left")
        tk.Radiobutton(class_frame, text="Text", variable=self.class_var, 
                      value=1, command=self.update_class).pack(side="left")
        
        self.help_label = tk.Label(info_frame, 
                                  text="Left-click: draw | Right-click: select | n: next | s: save | d: delete last | q: quit",
                                  font=("Arial", 10))
        self.help_label.pack(side="right")
        
        self.canvas = tk.Canvas(root, cursor="crosshair", bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.root.bind('<Key-n>', self.next_image)
        self.root.bind('<Key-s>', self.save_boxes)
        self.root.bind('<Key-d>', self.delete_last_box)
        self.root.bind('<Key-q>', lambda e: self.root.quit())
        
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Add right-click selector
        self.canvas.bind('<Button-3>', self.on_right_click)
        
        if images:
            self.load_image()
        else:
            self.status_label.config(text="No image found in the folder!")
    
    def update_class(self):
        """Updates the current class selected by the user"""
        self.current_class = self.class_var.get()
        
    def load_image(self):
        """Loads the current image and checks if annotations already exist"""
        self.canvas.delete("all")
        self.boxes = []
        self.box_objects = []
        
        img_path = self.images[self.current_index]
        img_name = os.path.basename(img_path)
        label_path = os.path.join(LABELS_DIR, os.path.splitext(img_name)[0] + '.txt')
        
        self.status_label.config(text=f"Image: {img_name} ({self.current_index+1}/{len(self.images)})")
        
        self.img = Image.open(img_path)
        self.width, self.height = self.img.size
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            scale = min(canvas_width / self.width, canvas_height / self.height)
            self.display_width = int(self.width * scale)
            self.display_height = int(self.height * scale)
            self.scale_factor = scale
            
            display_img = self.img.resize((self.display_width, self.display_height), Image.LANCZOS)
        else:
            display_img = self.img
            self.display_width, self.display_height = self.width, self.height
            self.scale_factor = 1.0
            
        self.img_tk = ImageTk.PhotoImage(display_img)
        self.canvas.config(width=self.display_width, height=self.display_height)
        self.canvas.create_image(0, 0, anchor='nw', image=self.img_tk)
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    try:
                        class_id, x_center, y_center, width, height = map(float, line.strip().split())
                        self.boxes.append((int(class_id), x_center, y_center, width, height))
                        self.draw_saved_box(int(class_id), x_center, y_center, width, height)
                    except ValueError:
                        print(f"Incorrect annotation format in {label_path}")
        
    def draw_saved_box(self, class_id, x_center, y_center, width, height):
        """Draws a saved box with resize handles"""
        x_center_px = x_center * self.width * self.scale_factor
        y_center_px = y_center * self.height * self.scale_factor
        width_px = width * self.width * self.scale_factor
        height_px = height * self.height * self.scale_factor
        
        x0 = x_center_px - width_px / 2
        y0 = y_center_px - height_px / 2
        x1 = x_center_px + width_px / 2
        y1 = y_center_px + height_px / 2
        
        # Choose color based on class
        color = 'green' if class_id == 0 else 'blue'
        
        # Create the box and store its canvas ID
        rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=f"box_{len(self.box_objects)}")
        
        # Create corner handles for resizing (initially hidden)
        handles = self.create_corner_handles(x0, y0, x1, y1, hidden=True)
        
        # Store the box and its handles
        self.box_objects.append({
            'rect_id': rect_id,
            'handles': handles,
            'coords': (x0, y0, x1, y1),
            'class_id': class_id
        })
        
    def create_corner_handles(self, x0, y0, x1, y1, hidden=False):
        """Create corner handles for resizing a box"""
        state = 'hidden' if hidden else 'normal'
        cs = self.corner_size
        
        tl = self.canvas.create_rectangle(x0-cs, y0-cs, x0+cs, y0+cs, fill='red', state=state, tags="handle")
        tr = self.canvas.create_rectangle(x1-cs, y0-cs, x1+cs, y0+cs, fill='red', state=state, tags="handle")
        bl = self.canvas.create_rectangle(x0-cs, y1-cs, x0+cs, y1+cs, fill='red', state=state, tags="handle")
        br = self.canvas.create_rectangle(x1-cs, y1-cs, x1+cs, y1+cs, fill='red', state=state, tags="handle")
        
        return {'tl': tl, 'tr': tr, 'bl': bl, 'br': br}
        
    def on_mouse_down(self, event):
        """Starts drawing a rectangle or begins resizing"""
        # Check if we're on a resize handle
        handle = self.canvas.find_withtag("current")
        if handle and "handle" in self.canvas.gettags(handle[0]):
            self.resize_handle = handle[0]
            return
            
        # Otherwise start a new rectangle
        self.start_x, self.start_y = event.x, event.y
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline='red', width=2
        )
        
    def on_mouse_drag(self, event):
        """Updates the rectangle during mouse movement or resizes existing box"""
        if self.resize_handle:
            # Resizing an existing box
            self.resize_box(event.x, event.y)
        elif self.current_rect:
            # Drawing a new box
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)
        
    def resize_box(self, x, y):
        """Resize the selected box based on which handle is being dragged"""
        if not self.selected_box:
            return
            
        box = self.box_objects[self.selected_box]
        x0, y0, x1, y1 = box['coords']
        
        # Find which handle is being dragged
        handle_id = self.resize_handle
        handles = box['handles']
        
        # Update coordinates based on which handle is being dragged
        if handle_id == handles['tl']:
            x0, y0 = x, y
        elif handle_id == handles['tr']:
            x1, y0 = x, y
        elif handle_id == handles['bl']:
            x0, y1 = x, y
        elif handle_id == handles['br']:
            x1, y1 = x, y
            
        # Ensure box has positive width and height
        if x1 <= x0:
            x0, x1 = x1, x0
        if y1 <= y0:
            y0, y1 = y1, y0
            
        # Update the box and handles
        self.canvas.coords(box['rect_id'], x0, y0, x1, y1)
        self.update_handle_positions(box, x0, y0, x1, y1)
        
        # Update the stored coordinates
        box['coords'] = (x0, y0, x1, y1)
        
        # Update the normalized coordinates in self.boxes
        self.update_box_data(self.selected_box, x0, y0, x1, y1)
        
    def update_handle_positions(self, box, x0, y0, x1, y1):
        """Update the positions of resize handles"""
        cs = self.corner_size
        handles = box['handles']
        
        self.canvas.coords(handles['tl'], x0-cs, y0-cs, x0+cs, y0+cs)
        self.canvas.coords(handles['tr'], x1-cs, y0-cs, x1+cs, y0+cs)
        self.canvas.coords(handles['bl'], x0-cs, y1-cs, x0+cs, y1+cs)
        self.canvas.coords(handles['br'], x1-cs, y1-cs, x1+cs, y1+cs)
        
    def update_box_data(self, box_index, x0, y0, x1, y1):
        """Update the normalized data for the modified box"""
        if 0 <= box_index < len(self.boxes):
            class_id = self.boxes[box_index][0]
            
            # Convert to normalized coordinates
            x0_norm = (x0 / self.scale_factor) / self.width
            y0_norm = (y0 / self.scale_factor) / self.height
            x1_norm = (x1 / self.scale_factor) / self.width
            y1_norm = (y1 / self.scale_factor) / self.height
            
            x_center = (x0_norm + x1_norm) / 2
            y_center = (y0_norm + y1_norm) / 2
            width = x1_norm - x0_norm
            height = y1_norm - y0_norm
            
            self.boxes[box_index] = (class_id, x_center, y_center, width, height)
        
    def on_mouse_up(self, event):
        """Finalizes the rectangle and saves the normalized coordinates"""
        if self.resize_handle:
            # End resizing
            self.resize_handle = None
            return
            
        if not self.current_rect:
            return
            
        end_x, end_y = event.x, event.y
        
        x0, x1 = sorted([self.start_x, end_x])
        y0, y1 = sorted([self.start_y, end_y])
        
        if (x1 - x0) < 5 or (y1 - y0) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return
            
        x0_norm = (x0 / self.scale_factor) / self.width
        y0_norm = (y0 / self.scale_factor) / self.height
        x1_norm = (x1 / self.scale_factor) / self.width
        y1_norm = (y1 / self.scale_factor) / self.height
        
        x_center = (x0_norm + x1_norm) / 2
        y_center = (y0_norm + y1_norm) / 2
        width = x1_norm - x0_norm
        height = y1_norm - y0_norm
        
        # Add box with current class
        self.boxes.append((self.current_class, x_center, y_center, width, height))
        
        # Delete the temporary rectangle
        self.canvas.delete(self.current_rect)
        
        # Create the permanent box with handles
        color = 'green' if self.current_class == 0 else 'blue'
        rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=f"box_{len(self.box_objects)}")
        handles = self.create_corner_handles(x0, y0, x1, y1, hidden=True)
        
        self.box_objects.append({
            'rect_id': rect_id,
            'handles': handles,
            'coords': (x0, y0, x1, y1),
            'class_id': self.current_class
        })
        
        self.current_rect = None
        
    def on_right_click(self, event):
        """Handle right-click to select a box"""
        # First, deselect any selected box
        if self.selected_box is not None:
            old_box = self.box_objects[self.selected_box]
            for handle_id in old_box['handles'].values():
                self.canvas.itemconfig(handle_id, state='hidden')
            self.selected_box = None
        
        # Find if we clicked on a box
        clicked_items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("box_"):
                    box_index = int(tag.split("_")[1])
                    self.selected_box = box_index
                    
                    # Show handles for the selected box
                    box = self.box_objects[box_index]
                    for handle_id in box['handles'].values():
                        self.canvas.itemconfig(handle_id, state='normal')
                    
                    # Update the class selector
                    self.class_var.set(box['class_id'])
                    self.current_class = box['class_id']
                    
                    # Change the outline to indicate selection
                    self.canvas.itemconfig(box['rect_id'], width=3)
                    return
        
    def save_boxes(self, event=None):
        """Saves annotations in YOLO format"""
        if not self.images:
            return
            
        img_path = self.images[self.current_index]
        img_name = os.path.basename(img_path)
        label_path = os.path.join(LABELS_DIR, os.path.splitext(img_name)[0] + '.txt')
        
        with open(label_path, 'w') as f:
            for box in self.boxes:
                class_id, x_center, y_center, width, height = box
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
        print(f"Annotations saved for {img_name}")
        
        # Count boxes by class
        bubbles = sum(1 for box in self.boxes if box[0] == 0)
        texts = sum(1 for box in self.boxes if box[0] == 1)
        self.status_label.config(text=f"Image: {img_name} | Saved: {bubbles} bubbles, {texts} texts")
        
    def next_image(self, event=None):
        """Saves and moves to the next image"""
        self.save_boxes()
        
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.load_image()
        else:
            print("End of images!")
            self.status_label.config(text="End of images! All annotations are saved.")
            
    def delete_last_box(self, event=None):
        """Deletes the last drawn box"""
        if self.boxes and self.box_objects:
            # If a box is selected, delete that one instead of the last one
            if self.selected_box is not None:
                # Get canvas IDs to delete
                box = self.box_objects[self.selected_box]
                self.canvas.delete(box['rect_id'])
                for handle_id in box['handles'].values():
                    self.canvas.delete(handle_id)
                
                # Remove from data structures
                self.box_objects.pop(self.selected_box)
                self.boxes.pop(self.selected_box)
                
                # Update tags for remaining boxes
                for i, box in enumerate(self.box_objects):
                    self.canvas.itemconfig(box['rect_id'], tags=f"box_{i}")
                    
                self.selected_box = None
            else:
                # Delete the last box
                last_box = self.box_objects.pop()
                self.canvas.delete(last_box['rect_id'])
                for handle_id in last_box['handles'].values():
                    self.canvas.delete(handle_id)
                self.boxes.pop()
            
def main():
    image_files = []
    for filename in sorted(os.listdir(IMAGES_DIR), key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else float('inf')):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_files.append(os.path.join(IMAGES_DIR, filename))
    
    if not image_files:
        print(f"No image found in {IMAGES_DIR}")
        return
        
    root = tk.Tk()
    app = BubbleAnnotator(root, image_files)
    
    root.update()
    app.load_image()
    
    root.mainloop()

if __name__ == "__main__":
    main()