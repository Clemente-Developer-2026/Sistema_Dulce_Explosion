from flask_login import UserMixin
from app.extensions import db

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)  
    telefono = db.Column(db.String, nullable=False)
    rol = db.Column(db.String, nullable=False)  
    password = db.Column(db.String, nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False)
    productos = db.relationship('Producto', back_populates='usuario', lazy=True, cascade="all, delete-orphan")
    def get_id(self):
        return str(self.id_usuario)
    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol,
            "fecha_registro": self.fecha_registro.strftime("%d/%m/%Y") if self.fecha_registro else None
        }
    
class Categoria(db.Model):
    __tablename__ = "categorias"  
    id_categoria = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String, nullable=False)
    productos = db.relationship('Producto', back_populates='categoria', lazy=True)

    def to_dict(self):
        return {
            "id_categoria": self.id_categoria,
            "categoria": self.categoria
        }

class Producto(db.Model):
    __tablename__ = "productos"
    id_producto = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)  
    descripcion = db.Column(db.String, nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)  
    usuario = db.relationship('Usuario', back_populates='productos')
    categoria = db.relationship('Categoria', back_populates='productos')
    imagenes = db.relationship('Imagen', back_populates='producto', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id_producto": self.id_producto,
            "producto": self.producto,
            "precio": self.precio,
            "stock": self.stock,
            "descripcion": self.descripcion,
            "id_usuario": self.id_usuario,
            "id_categoria": self.id_categoria,  
            "categoria": self.categoria.categoria if self.categoria else None  
        }

class Imagen(db.Model):
    __tablename__ = "imagenes"
    id_imagen = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(255), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    producto = db.relationship('Producto', back_populates='imagenes')
    
    def to_dict(self):
        return {
            "id_imagen": self.id_imagen,
            "imagen": self.imagen,
            "id_producto": self.id_producto
        }