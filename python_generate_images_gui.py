import os
import sys
import subprocess
import requests
import logging
import numpy as np
import cv2
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import io

# Current script version
SCRIPT_VERSION = "1.0.0"

# URLs for the remote script and version file
# Replace 'your-username' with your actual GitHub username
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/your-username/image-generation-script/main/version.txt"
REMOTE_SCRIPT_URL = "https://raw.githubusercontent.com/your-username/image-generation-script/main/python_generate_images_gui.py"

# Set up logging
logging.basicConfig(
    filename=r"C:\Users\SeNtRy\Desktop\script_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Project-specific paths
BASE_DIR = Path(r"C:\Users\SeNtRy\Desktop\Generated_(A História Inspiradora de Jó  Mantendo a Fé nas Adversidades)")
PROMPTS_FILE = BASE_DIR / "(A História Inspiradora de Jó  Mantendo a Fé nas Adversidades)_prompts.txt"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Scene durations (in seconds) as extracted from the log
SCENE_DURATIONS = [
    14, 10, 12, 14, 11, 12, 10, 15, 10, 13, 14, 15, 8, 6, 12, 10, 10, 9, 7, 10,
    9, 15, 7, 11, 8, 9, 8, 9, 15, 12, 15, 12, 8, 7, 11, 4, 12, 14, 10, 10, 10,
    10, 10, 8, 9, 7, 12, 9, 10, 7, 8, 13, 5, 12, 14, 9, 10, 10, 10, 10, 8, 9, 7,
    12, 9, 11, 8, 8, 13, 6, 11, 14, 9, 10, 10, 10, 10, 8, 9, 7, 12, 9, 12, 12, 12,
    9, 9, 12, 6, 12, 9, 7, 12, 13, 7, 7
]

# Available styles and genres
STYLE_OPTIONS = ["Sacred Realism", "Renaissance", "Baroque", "Photorealistic", "Oil Painting"]
GENRE_OPTIONS = ["Historical", "Biblical", "Epic", "Dramatic"]

# Available aspect ratios and their corresponding ratios
ASPECT_RATIOS = {
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:2": (3, 2),
    "16:9": (16, 9),
    "9:16": (9, 16),
    "3:4": (3, 4),
    "2:3": (2, 3)
}

# Available formats
FORMAT_OPTIONS = ["PNG", "JPEG"]

def check_for_updates():
    """Check for updates and update the script if a new version is available."""
    try:
        logging.info("Checking for updates...")
        response = requests.get(REMOTE_VERSION_URL, timeout=5)
        response.raise_for_status()
        remote_version = response.text.strip()

        if remote_version != SCRIPT_VERSION:
            logging.info(f"New version found: {remote_version} (current: {SCRIPT_VERSION})")
            messagebox.showinfo("Atualização Disponível", f"Uma nova versão ({remote_version}) está disponível. Atualizando...")

            script_response = requests.get(REMOTE_SCRIPT_URL, timeout=5)
            script_response.raise_for_status()
            new_script_content = script_response.text

            with open(__file__, "w", encoding="utf-8") as f:
                f.write(new_script_content)
            logging.info("Script updated successfully.")

            logging.info("Restarting script to apply update...")
            subprocess.run([sys.executable, __file__])
            sys.exit(0)
        else:
            logging.info("No updates available. Running current version.")
    except Exception as e:
        logging.error(f"Failed to check for updates: {str(e)}")
        messagebox.showwarning("Aviso", f"Não foi possível verificar atualizações: {str(e)}. Continuando com a versão atual.")

def calculate_resolution(aspect_ratio, max_dimension=1920):
    """Calculate the resolution based on the selected aspect ratio, with the longer side as max_dimension."""
    ratio_width, ratio_height = ASPECT_RATIOS[aspect_ratio]
    if ratio_width >= ratio_height:
        width = max_dimension
        height = int(max_dimension * ratio_height / ratio_width)
    else:
        height = max_dimension
        width = int(max_dimension * ratio_width / ratio_height)
    return width, height

def remove_watermark(image):
    """Remove the Pollinations.ai watermark from the image using inpainting."""
    # Convert PIL image to OpenCV format (numpy array)
    image_np = np.array(image)
    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Create a mask for the watermark (assumed to be in the bottom-right corner)
    height, width = image_np.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)

    # Define the watermark area (adjust these values based on the actual watermark position)
    # Assuming the watermark is approximately 200x50 pixels in the bottom-right corner
    watermark_width, watermark_height = 200, 50
    x_start = width - watermark_width - 10  # 10 pixels padding from the edge
    y_start = height - watermark_height - 10
    mask[y_start:y_start + watermark_height, x_start:x_start + watermark_width] = 255

    # Apply inpainting to remove the watermark
    inpainted_image = cv2.inpaint(image_np, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Convert back to PIL image
    inpainted_image = cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(inpainted_image)

def generate_image_with_pollinations(prompt, width, height, scene_num, image_format):
    """Generate an image using Pollinations.ai API and remove the watermark."""
    output_path = BASE_DIR / f"scene_{scene_num:02d}.{image_format.lower()}"
    negative_prompt = "blurry, low quality, distorted, modern elements, unrealistic, overexposed, underexposed, anachronistic objects, modern clothing, technology"

    # Pollinations.ai API URL
    api_url = "https://pollinations.ai/prompt"
    params = {
        "prompt": f"{prompt}, --ar {width}:{height} --negative {negative_prompt}",
        "width": width,
        "height": height
    }

    for attempt in range(1, 6):  # 5 retries
        try:
            logging.info(f"Attempt {attempt} to generate image {scene_num} with Pollinations.ai...")
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()

            # Pollinations.ai returns the image directly
            image = Image.open(io.BytesIO(response.content))

            # Remove the watermark
            logging.info(f"Removing watermark from image {scene_num}...")
            image = remove_watermark(image)

            # Save in the selected format
            if image_format == "JPEG":
                image = image.convert("RGB")  # Ensure RGB mode for JPEG
                image.save(output_path, quality=95)
            else:
                image.save(output_path)

            logging.info(f"Image {scene_num} generated successfully: {output_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to generate image {scene_num} on attempt {attempt}: {str(e)}")
    logging.error(f"Failed to generate image {scene_num} after 5 attempts.")
    return False

def parse_text_to_scenes(text_content, num_scenes):
    """Parse the text content into segments for each scene."""
    # Split the text into lines or paragraphs
    lines = text_content.split("\n")
    lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines

    # If the text has fewer segments than scenes, repeat or pad the content
    if len(lines) < num_scenes:
        lines = (lines * (num_scenes // len(lines) + 1))[:num_scenes]
    elif len(lines) > num_scenes:
        # If there are more lines than scenes, combine lines
        lines_per_scene = len(lines) // num_scenes
        new_lines = []
        for i in range(0, len(lines), lines_per_scene):
            segment = " ".join(lines[i:i + lines_per_scene])
            new_lines.append(segment)
        lines = new_lines[:num_scenes]

    return lines

def generate_prompt_from_text(segment, scene_num, style, genre):
    """Generate a detailed prompt based on the text segment for a given scene."""
    # Base description of Job, ensuring historical accuracy
    base_desc = (
        f"Job, an elderly man with long gray hair, a full white beard, wearing a simple beige tunic and a red cape, "
        f"standing with a {'sorrowful' if scene_num == 34 else 'neutral'} expression, full-body view, ultra-detailed, "
        f"cinematic lighting, natural pose, vibrant colors, dramatic shadows, realistic textures, no modern elements, "
        f"biblical era clothing, ancient Middle Eastern setting"
    )

    # Vary the landscape
    landscape = "desert with distant mountains" if scene_num in [50, 67] else "ancient Middle Eastern landscape with rocky terrain and sparse vegetation"

    # Vary the pose or lighting for diversity
    variation = (
        "looking slightly to the left, soft sunlight casting gentle shadows" if scene_num % 3 == 0 else
        "facing forward, golden hour lighting with warm tones" if scene_num % 3 == 1 else
        "slight profile view, dramatic sunset with deep orange and purple hues"
    )

    # Incorporate the text segment into the prompt
    context = f"depicting a moment where {segment.lower()}" if segment else "in a moment of reflection"

    # Construct the prompt
    prompt = (
        f"A {style.lower()} {genre.lower()} scene in a {landscape}, featuring {base_desc}, {context}, {variation}, "
        f"inspired by {style.lower()} paintings, sacred atmosphere, highly detailed, historically accurate, "
        f"no anachronisms, biblical era setting"
    )
    return prompt

class ImageGenerationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Imagens - A História Inspiradora de Jó")
        self.root.geometry("600x600")
        self.text_file = None
        self.text_content = None

        # Variables for user selections
        self.style_var = tk.StringVar(value=STYLE_OPTIONS[0])
        self.genre_var = tk.StringVar(value=GENRE_OPTIONS[0])
        self.aspect_ratio_var = tk.StringVar(value="16:9")
        self.format_var = tk.StringVar(value=FORMAT_OPTIONS[0])

        # GUI Elements
        tk.Label(root, text="Configurações de Geração de Imagens", font=("Arial", 16)).pack(pady=10)

        # Select Text File
        tk.Button(root, text="Selecionar Arquivo de Texto", command=self.select_text_file, font=("Arial", 12)).pack(pady=5)

        # Style Selection
        tk.Label(root, text="Estilo:", font=("Arial", 12)).pack()
        ttk.Combobox(root, textvariable=self.style_var, values=STYLE_OPTIONS, state="readonly").pack()

        # Genre Selection
        tk.Label(root, text="Gênero:", font=("Arial", 12)).pack()
        ttk.Combobox(root, textvariable=self.genre_var, values=GENRE_OPTIONS, state="readonly").pack()

        # Aspect Ratio Selection
        tk.Label(root, text="Proporção (Aspect Ratio):", font=("Arial", 12)).pack()
        ttk.Combobox(root, textvariable=self.aspect_ratio_var, values=list(ASPECT_RATIOS.keys()), state="readonly").pack()

        # Format Selection
        tk.Label(root, text="Formato:", font=("Arial", 12)).pack()
        ttk.Combobox(root, textvariable=self.format_var, values=FORMAT_OPTIONS, state="readonly").pack()

        # Start Button
        tk.Button(root, text="Iniciar Geração de Imagens", command=self.start_generation, font=("Arial", 14)).pack(pady=20)

    def select_text_file(self):
        """Allow the user to select a text file containing the narration or script."""
        file_path = filedialog.askopenfilename(
            title="Selecionar Arquivo de Texto",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.text_file = file_path
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.text_content = f.read()
                messagebox.showinfo("Sucesso", f"Arquivo selecionado: {file_path}")
            except Exception as e:
                logging.error(f"Failed to read text file: {str(e)}")
                messagebox.showerror("Erro", f"Não foi possível ler o arquivo: {str(e)}")
                self.text_file = None
                self.text_content = None

    def save_prompts(self, scenes):
        """Save all prompts to a file."""
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            for scene_num, (prompt, duration) in enumerate(scenes, 1):
                f.write(f"Prompt para Scene {scene_num:02d} ({duration}s): {prompt}\n")
                f.write(f"Número de tokens: {len(prompt.split())}\n")
        logging.info(f"Prompts saved to: {PROMPTS_FILE}")

    def start_generation(self):
        """Main function to generate images for all scenes."""
        try:
            logging.info("Verificando dependências...")
            logging.info("Abrindo a interface gráfica...")

            if not self.text_file or not self.text_content:
                messagebox.showerror("Erro", "Por favor, selecione um arquivo de texto antes de iniciar a geração.")
                return

            # Parse the text into segments for each scene
            text_segments = parse_text_to_scenes(self.text_content, len(SCENE_DURATIONS))

            # Parse aspect ratio and calculate resolution
            aspect_ratio = self.aspect_ratio_var.get()
            width, height = calculate_resolution(aspect_ratio, max_dimension=1920)
            logging.info(f"Resolução calculada: {width}x{height} (Aspect Ratio: {aspect_ratio})")

            # Create scenes list with prompts
            scenes = []
            style = self.style_var.get()
            genre = self.genre_var.get()
            for scene_num, (duration, segment) in enumerate(zip(SCENE_DURATIONS, text_segments), 1):
                prompt = generate_prompt_from_text(segment, scene_num, style, genre)
                scenes.append((prompt, duration))

            # Log scene details
            total_duration = sum(SCENE_DURATIONS)
            logging.info(f"Tempo estimado de narração: {total_duration} segundos")
            logging.info(f"Gênero selecionado: {genre.lower()}")
            logging.info(f"Segmentos criados: {len(scenes)}")

            # Save prompts to file
            self.save_prompts(scenes)

            # Generate images for each scene using Pollinations.ai
            for scene_num, (prompt, duration) in enumerate(scenes, 1):
                logging.info(f"Gerando imagem {scene_num}/{len(scenes)}: Scene {scene_num:02d} ({duration}s)")
                success = generate_image_with_pollinations(prompt, width, height, scene_num, self.format_var.get())
                if not success:
                    messagebox.showerror(
                        "Erro",
                        f"Não foi possível gerar a imagem para Scene {scene_num} após várias tentativas. Verifique o log para detalhes."
                    )
                    return

            messagebox.showinfo("Sucesso", "Geração de imagens concluída! Verifique o log para detalhes.")
        except Exception as e:
            logging.error(f"Erro durante a execução: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}. Verifique o log para detalhes.")
        finally:
            self.root.destroy()

if __name__ == "__main__":
    # Check for updates before starting the app
    check_for_updates()

    # Start the application
    root = tk.Tk()
    app = ImageGenerationApp(root)
    root.mainloop()