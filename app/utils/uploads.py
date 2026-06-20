import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_url(filename):
    if filename:
        return f"/static/uploads/{filename}"
    return None

def save_image(file):
    if not file:
        return False, None, "No se recibió ningún archivo"
    
    if file.filename == '':
        return False, None, "No se seleccionó ningún archivo"
    
    if not allowed_file(file.filename):
        return False, None, f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
    
    try:
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return True, unique_filename, "Imagen guardada exitosamente"
    except Exception as e:
        return False, None, f"Error al guardar la imagen: {str(e)}"

def delete_image(filename):
    if not filename:
        return True, "No se eliminó ninguna imagen"
    try:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, "Imagen eliminada exitosamente"
        else:
            return True, "La imagen no existe en el servidor"
    
    except Exception as e:
        return False, f"Error al eliminar la imagen: {str(e)}"