import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
from tkinter import ttk
import tkinter.font as tkfont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image
import qrcode
import io
import math  # Imported math for ceiling function

# Helper functions for unit conversion
def mm_to_points(mm_value):
    return mm_value * 72 / 25.4

def points_to_mm(points_value):
    return points_value * 25.4 / 72

def generate_pdf(part_numbers, settings):
    try:
        # Create a PDF canvas
        c = canvas.Canvas(settings['output_file'], pagesize=letter)
        page_width, page_height = letter  # in points

        # Unpack settings
        left_margin = mm_to_points(float(settings['left_margin']))
        top_margin = mm_to_points(float(settings['top_margin']))
        label_width = mm_to_points(float(settings['label_width']))
        label_height = mm_to_points(float(settings['label_height']))
        x_pitch = mm_to_points(float(settings['x_pitch']))
        y_pitch = mm_to_points(float(settings['y_pitch']))
        labels_x = int(settings['labels_x'])
        labels_y = int(settings['labels_y'])
        draw_rectangles = settings['draw_rectangles']
        center_horizontally = settings['center_horizontally']
        center_vertically = settings['center_vertically']
        start_index = int(settings['start_index'])
        dynamic_text_size = settings['dynamic_text_size']
        enable_qr = settings['enable_qr']
        font_size = int(settings['font_size'])
        font_family = settings['font_family']
        font_bold = settings['font_bold']
        font_italic = settings['font_italic']
        font_color = settings['font_color']
        text_justification = settings['text_justification']

        # Validate Label Start Index
        labels_per_sheet = labels_x * labels_y
        if start_index < 0 or start_index >= labels_per_sheet:
            messagebox.showerror("Error", f"Label Start Index must be between 0 and {labels_per_sheet - 1}.")
            return

        # Calculate total number of sheets required
        total_part_numbers = len(part_numbers)
        labels_available_first_sheet = labels_per_sheet - start_index
        remaining_labels = total_part_numbers - labels_available_first_sheet

        if remaining_labels <= 0:
            total_sheets = 1
        else:
            total_sheets = 1 + math.ceil(remaining_labels / labels_per_sheet)

        # Unpack font settings
        font_name = font_family
        if font_bold and font_italic:
            font_name += '-BoldOblique'
        elif font_bold:
            font_name += '-Bold'
        elif font_italic:
            font_name += '-Oblique'

        # Adjust margins for centering
        total_label_width = (labels_x - 1) * x_pitch + label_width
        total_label_height = (labels_y - 1) * y_pitch + label_height

        if center_horizontally:
            left_margin = (page_width - total_label_width) / 2

        if center_vertically:
            top_margin = (page_height - total_label_height) / 2

        # Initialize part index
        part_index = 0
        sheet_number = 1

        while part_index < total_part_numbers:
            for label_pos in range(labels_per_sheet):
                # Skip labels before start_index on the first sheet
                if sheet_number == 1 and label_pos < start_index:
                    continue

                if part_index >= total_part_numbers:
                    break

                # Calculate row and column based on label position
                row = label_pos // labels_x
                col = label_pos % labels_x

                # Calculate label position
                x_position = left_margin + col * x_pitch
                y_position = page_height - (top_margin + row * y_pitch + label_height)

                # Draw debugging rectangle if option is selected
                if draw_rectangles:
                    c.roundRect(x_position, y_position, label_width, label_height, radius=5, stroke=1, fill=0)

                part = part_numbers[part_index]
                if part.strip() != '':
                    # Define padding
                    padding = mm_to_points(1)  # 1 mm padding
                    content_width = label_width - 2 * padding

                    if enable_qr:
                        # Generate QR code with optimized parameters
                        qr = qrcode.QRCode(
                            version=None,  # Let qrcode determine the smallest version possible
                            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
                            box_size=8,  # Adjust box_size for better readability
                            border=4,  # Adequate border
                        )
                        qr.add_data(part)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img_reader = ImageReader(img_buffer)

                        qr_size = label_height - 2 * padding
                        c.drawImage(
                            img_reader,
                            x_position + padding,
                            y_position + padding,
                            width=qr_size,
                            height=qr_size
                        )

                        text_x = x_position + padding + qr_size + mm_to_points(1)  # Additional 1 mm spacing
                        available_width = content_width - qr_size - mm_to_points(1)
                    else:
                        # QR codes disabled; draw text in place of QR code
                        text_x = x_position + padding
                        available_width = content_width

                    # Draw part number text
                    text_y = y_position + label_height / 2 - font_size / 2  # Adjust text position

                    # Dynamic text size
                    current_font_size = font_size
                    if dynamic_text_size:
                        text_width = c.stringWidth(part[:40], font_name, current_font_size)
                        while text_width > available_width and current_font_size > 6:
                            current_font_size -= 0.5
                            text_width = c.stringWidth(part[:40], font_name, current_font_size)
                        c.setFont(font_name, current_font_size)
                    else:
                        c.setFont(font_name, current_font_size)

                    # Set font color
                    try:
                        c.setFillColor(font_color)
                    except:
                        c.setFillColor("black")  # Fallback to black if color is invalid

                    # Handle text justification
                    if text_justification == 'Left':
                        c.drawString(text_x, text_y, part[:40])  # Ensure max 40 characters
                    elif text_justification == 'Center':
                        center_x = x_position + label_width / 2
                        c.drawCentredString(center_x, text_y, part[:40])
                    elif text_justification == 'Right':
                        right_x = x_position + label_width - padding
                        c.drawRightString(right_x, text_y, part[:40])

                    # Reset fill color to black
                    c.setFillColor("black")

                part_index += 1

            if part_index < total_part_numbers:
                # More part numbers to process, create a new page
                c.showPage()
                sheet_number += 1
                # Reset start_index for new pages
                start_index = 0
                # Adjust margins again if centering is enabled
                if center_horizontally:
                    left_margin = (page_width - total_label_width) / 2
                if center_vertically:
                    top_margin = (page_height - total_label_height) / 2
            else:
                break  # All part numbers processed

        c.save()
        messagebox.showinfo("Success", f"PDF generated successfully at:\n{settings['output_file']}\nNumber of sheets required: {total_sheets}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_preview(event=None):
    # Clear the canvas
    preview_canvas.delete('all')

    # Get settings from input fields
    try:
        left_margin = mm_to_points(float(left_margin_var.get()))
        top_margin = mm_to_points(float(top_margin_var.get()))
        label_width = mm_to_points(float(label_width_var.get()))
        label_height = mm_to_points(float(label_height_var.get()))
        x_pitch = mm_to_points(float(x_pitch_var.get()))
        y_pitch = mm_to_points(float(y_pitch_var.get()))
        labels_x = int(labels_x_var.get())
        labels_y = int(labels_y_var.get())
        center_horizontally = center_horizontally_var.get()
        center_vertically = center_vertically_var.get()
        start_index = int(label_start_index_var.get())
        enable_qr = enable_qr_var.get()
    except ValueError:
        # Invalid input; do not update preview
        return

    page_width, page_height = letter  # in points

    canvas_width = preview_canvas.winfo_width()
    canvas_height = preview_canvas.winfo_height()

    # Ensure canvas has a size
    if canvas_width < 10 or canvas_height < 10:
        # Canvas hasn't been properly initialized yet
        preview_canvas.after(100, update_preview)
        return

    scale_x = canvas_width / page_width
    scale_y = canvas_height / page_height

    scale = min(scale_x, scale_y)

    # Adjust margins for centering
    total_label_width = (labels_x -1) * x_pitch + label_width
    total_label_height = (labels_y -1) * y_pitch + label_height

    if center_horizontally:
        left_margin_scaled = (page_width - total_label_width) / 2 * scale
    else:
        left_margin_scaled = left_margin * scale

    if center_vertically:
        top_margin_scaled = (page_height - total_label_height) / 2 * scale
    else:
        top_margin_scaled = top_margin * scale

    # Draw labels
    label_count = labels_x * labels_y
    for i in range(label_count):
        row = i // labels_x
        col = i % labels_x
        x_position = left_margin_scaled + col * x_pitch * scale
        y_position = top_margin_scaled + row * y_pitch * scale

        # Draw rectangle
        preview_canvas.create_rectangle(
            x_position,
            y_position,
            x_position + label_width * scale,
            y_position + label_height * scale,
            outline='black'
        )

        # Determine if this label is skipped
        if i < start_index:
            # Draw red X over the label
            preview_canvas.create_line(
                x_position, y_position,
                x_position + label_width * scale, y_position + label_height * scale,
                fill='red', width=2
            )
            preview_canvas.create_line(
                x_position, y_position + label_height * scale,
                x_position + label_width * scale, y_position,
                fill='red', width=2
            )
        else:
            # Optionally draw QR code or text placeholder
            padding = mm_to_points(1) * scale
            qr_size = label_height * scale - 2 * padding

            if enable_qr:
                # Draw QR code placeholder
                preview_canvas.create_rectangle(
                    x_position + padding,
                    y_position + padding,
                    x_position + padding + qr_size,
                    y_position + padding + qr_size,
                    fill='gray'
                )
            else:
                # Draw text placeholder where QR code would be
                preview_canvas.create_text(
                    x_position + padding + qr_size / 2,
                    y_position + padding + qr_size / 2,
                    text="Text",
                    anchor='center',
                    font=('Helvetica', int(6 * scale))
                )

            # Draw part number placeholder (e.g., label index)
            part = str(i - start_index)
            text_x = x_position + padding + qr_size + mm_to_points(1) * scale  # Additional 1 mm spacing
            text_y = y_position + label_height * scale / 2
            preview_canvas.create_text(
                text_x,
                text_y,
                text=part,
                anchor='w',
                font=('Helvetica', int(6 * scale))
            )

    # Update the canvas
    preview_canvas.update()

def on_variable_change(*args):
    update_preview()

def on_generate():
    # Get part numbers from text field
    part_numbers = text_input.get("1.0", tk.END).strip().split('\n')
    part_numbers = [p.strip() for p in part_numbers if p.strip() != '']

    # Get settings from input fields
    settings = {
        'left_margin': left_margin_var.get(),
        'top_margin': top_margin_var.get(),
        'label_width': label_width_var.get(),
        'label_height': label_height_var.get(),
        'x_pitch': x_pitch_var.get(),
        'y_pitch': y_pitch_var.get(),
        'labels_x': labels_x_var.get(),
        'labels_y': labels_y_var.get(),
        'draw_rectangles': draw_rectangles_var.get(),
        'center_horizontally': center_horizontally_var.get(),
        'center_vertically': center_vertically_var.get(),
        'start_index': label_start_index_var.get(),
        'dynamic_text_size': dynamic_text_size_var.get(),
        'enable_qr': enable_qr_var.get(),
        'font_size': font_size_var.get(),
        'font_family': font_family_var.get(),
        'font_bold': font_bold_var.get(),
        'font_italic': font_italic_var.get(),
        'font_color': font_color_var.get(),
        'text_justification': text_justification_var.get(),
        'output_file': filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    }

    if not settings['output_file']:
        return  # User cancelled the file dialog

    generate_pdf(part_numbers, settings)
    update_preview()

def on_escape(event):
    root.quit()

def on_ctrl_s(event):
    on_generate()

def choose_color():
    color_code = colorchooser.askcolor(title="Choose Font Color")
    if color_code and color_code[1]:
        font_color_var.set(color_code[1])

# Create the main window
root = tk.Tk()
root.title("Label QR Code Generator")
root.geometry("1200x700")  # Set a reasonable default size

# Configure grid weights to allow resizing
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# Top Frame for Part Numbers and Preview
frame_top = ttk.Frame(root)
frame_top.grid(row=0, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
frame_top.grid_rowconfigure(1, weight=1)
frame_top.grid_columnconfigure(0, weight=1)
frame_top.grid_columnconfigure(1, weight=1)

# Part numbers input
ttk.Label(frame_top, text="Enter part numbers (one per line, max 40 characters):").grid(row=0, column=0, sticky='w')
text_input = tk.Text(frame_top, width=50, height=20)
text_input.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

# Preview Canvas
ttk.Label(frame_top, text="Preview:").grid(row=0, column=1, sticky='w')
preview_canvas = tk.Canvas(frame_top, bg='white')
preview_canvas.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

# Bind the configure event to update the preview when the canvas is resized
preview_canvas.bind("<Configure>", update_preview)

# Bottom Frame for Settings
frame_bottom = ttk.Frame(root)
frame_bottom.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
frame_bottom.grid_columnconfigure(0, weight=1)
frame_bottom.grid_columnconfigure(1, weight=1)
frame_bottom.grid_columnconfigure(2, weight=1)

# Miscellaneous Settings
frame_misc = ttk.LabelFrame(frame_bottom, text="Miscellaneous Settings")
frame_misc.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

enable_qr_var = tk.BooleanVar(value=True)
enable_qr_check = ttk.Checkbutton(frame_misc, text="Enable QR Codes", variable=enable_qr_var)
enable_qr_check.grid(row=0, column=0, sticky='w', padx=5, pady=2)

draw_rectangles_var = tk.BooleanVar()
draw_rectangles_check = ttk.Checkbutton(frame_misc, text="Draw Rounded Rectangles (Debug)", variable=draw_rectangles_var)
draw_rectangles_check.grid(row=1, column=0, sticky='w', padx=5, pady=2)

center_horizontally_var = tk.BooleanVar(value=True)  # Set to True by default
center_horizontally_check = ttk.Checkbutton(frame_misc, text="Center Horizontally", variable=center_horizontally_var)
center_horizontally_check.grid(row=2, column=0, sticky='w', padx=5, pady=2)

center_vertically_var = tk.BooleanVar(value=True)  # Set to True by default
center_vertically_check = ttk.Checkbutton(frame_misc, text="Center Vertically", variable=center_vertically_var)
center_vertically_check.grid(row=3, column=0, sticky='w', padx=5, pady=2)

dynamic_text_size_var = tk.BooleanVar()
dynamic_text_size_check = ttk.Checkbutton(frame_misc, text="Dynamic Text Size", variable=dynamic_text_size_var)
dynamic_text_size_check.grid(row=4, column=0, sticky='w', padx=5, pady=2)

# Grid Adjustment Parameters
frame_grid = ttk.LabelFrame(frame_bottom, text="Grid Adjustment Parameters (mm)")
frame_grid.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
frame_grid.grid_columnconfigure(0, weight=1)
frame_grid.grid_columnconfigure(1, weight=1)

left_margin_var = tk.StringVar(value="4.05")
top_margin_var = tk.StringVar(value="12.837")
label_width_var = tk.StringVar(value="44.24")
label_height_var = tk.StringVar(value="12.47")
x_pitch_var = tk.StringVar(value="51.95")
y_pitch_var = tk.StringVar(value="12.6863")
labels_x_var = tk.StringVar(value="4")
labels_y_var = tk.StringVar(value="20")
label_start_index_var = tk.StringVar(value="0")

ttk.Label(frame_grid, text="Left Margin:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=left_margin_var, width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Top Margin:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=top_margin_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Label Width:").grid(row=2, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=label_width_var, width=10).grid(row=2, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Label Height:").grid(row=3, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=label_height_var, width=10).grid(row=3, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="X Pitch:").grid(row=4, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=x_pitch_var, width=10).grid(row=4, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Y Pitch:").grid(row=5, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=y_pitch_var, width=10).grid(row=5, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Labels in X:").grid(row=6, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=labels_x_var, width=10).grid(row=6, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Labels in Y:").grid(row=7, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=labels_y_var, width=10).grid(row=7, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_grid, text="Label Start Index:").grid(row=8, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_grid, textvariable=label_start_index_var, width=10).grid(row=8, column=1, sticky='w', padx=5, pady=2)

# Font Settings
frame_font = ttk.LabelFrame(frame_bottom, text="Font Settings")
frame_font.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
frame_font.grid_columnconfigure(0, weight=1)
frame_font.grid_columnconfigure(1, weight=1)

font_size_var = tk.StringVar(value="12")  # Increased default font size
font_family_var = tk.StringVar(value="Helvetica")
font_bold_var = tk.BooleanVar()
font_italic_var = tk.BooleanVar()
font_color_var = tk.StringVar(value="black")
text_justification_var = tk.StringVar(value="Left")

# Get available font families
available_fonts = sorted(tkfont.families())

ttk.Label(frame_font, text="Font Size:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
ttk.Entry(frame_font, textvariable=font_size_var, width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_font, text="Font Family:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
font_family_menu = ttk.Combobox(frame_font, textvariable=font_family_var, values=available_fonts, state="readonly", width=12)
font_family_menu.grid(row=1, column=1, sticky='w', padx=5, pady=2)
font_family_menu.set("Helvetica")  # Set default value

font_bold_check = ttk.Checkbutton(frame_font, text="Bold", variable=font_bold_var)
font_bold_check.grid(row=2, column=0, sticky='w', padx=5, pady=2)

font_italic_check = ttk.Checkbutton(frame_font, text="Italic", variable=font_italic_var)
font_italic_check.grid(row=2, column=1, sticky='w', padx=5, pady=2)

ttk.Label(frame_font, text="Font Color:").grid(row=3, column=0, sticky='e', padx=5, pady=2)
frame_font_color = ttk.Frame(frame_font)
frame_font_color.grid(row=3, column=1, sticky='w', padx=5, pady=2)
ttk.Entry(frame_font_color, textvariable=font_color_var, width=10).grid(row=0, column=0, sticky='w')
ttk.Button(frame_font_color, text="Choose", command=choose_color).grid(row=0, column=1, sticky='w', padx=5)

ttk.Label(frame_font, text="Justification:").grid(row=4, column=0, sticky='e', padx=5, pady=2)
justification_options = ["Left", "Center", "Right"]
justification_menu = ttk.OptionMenu(frame_font, text_justification_var, "Left", *justification_options)
justification_menu.grid(row=4, column=1, sticky='w', padx=5, pady=2)

# Add red note above the generate button
note_text = (
    "Place in bypass tray with the label side down and with its header facing away from the printer.\n"
    "Before printing ensure to print black and white to the bypass tray and set page sizing to Actual Size."
)
note_label = ttk.Label(root, text=note_text, foreground='red', justify='center')
note_label.grid(row=2, column=0, columnspan=3, pady=(0, 5))

# Generate button
generate_button = ttk.Button(root, text="Generate PDF", command=on_generate)
generate_button.grid(row=3, column=0, columnspan=3, pady=10)

# Bind keys
root.bind('<Escape>', on_escape)
root.bind('<Control-s>', on_ctrl_s)

# Trace variables to update preview
variables_to_trace = [
    left_margin_var, top_margin_var, label_width_var, label_height_var,
    x_pitch_var, y_pitch_var, labels_x_var, labels_y_var,
    center_horizontally_var, center_vertically_var, draw_rectangles_var,
    label_start_index_var, enable_qr_var, font_size_var, font_family_var,
    font_bold_var, font_italic_var, font_color_var, text_justification_var
]

for var in variables_to_trace:
    var.trace_add('write', on_variable_change)

# Initial update of preview
root.after(100, update_preview)

root.mainloop()
