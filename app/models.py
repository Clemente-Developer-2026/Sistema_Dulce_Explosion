from flask_login import UserMixin
from app.extensions import db
from datetime import datetime

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
    pedidos = db.relationship('Pedido', back_populates='usuario', lazy=True, cascade="all, delete-orphan")
    favoritos = db.relationship('Favorito', back_populates='usuario', lazy=True, cascade="all, delete-orphan")
    carrito = db.relationship('Carrito', back_populates='usuario', lazy=True, cascade="all, delete-orphan")
    
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
    detalle_pedidos = db.relationship('DetallePedido', back_populates='producto', lazy=True, cascade="all, delete-orphan")
    favoritos = db.relationship('Favorito', back_populates='producto', lazy=True, cascade="all, delete-orphan")
    carrito_items = db.relationship('CarritoItem', back_populates='producto', lazy=True, cascade="all, delete-orphan")
    catalogos = db.relationship('CatalogoProducto', back_populates='producto', lazy=True, cascade="all, delete-orphan")

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

class Catalogo(db.Model):
    __tablename__ = "catalogos"
    id_catalogo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    activo = db.Column(db.Boolean, default=True)
    imagen = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    productos = db.relationship('CatalogoProducto', back_populates='catalogo', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id_catalogo": self.id_catalogo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "fecha_inicio": self.fecha_inicio.strftime("%d/%m/%Y %H:%M") if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.strftime("%d/%m/%Y %H:%M") if self.fecha_fin else None,
            "activo": self.activo,
            "imagen": self.imagen,
            "productos": [cp.producto.to_dict() for cp in self.productos] if self.productos else []
        }


class CatalogoProducto(db.Model):
    __tablename__ = "catalogo_productos"
    id = db.Column(db.Integer, primary_key=True)
    id_catalogo = db.Column(db.Integer, db.ForeignKey('catalogos.id_catalogo'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    orden = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    catalogo = db.relationship('Catalogo', back_populates='productos')
    producto = db.relationship('Producto', back_populates='catalogos')  # ✅ Ahora existe en Producto
    
    def to_dict(self):
        return {
            "id": self.id,
            "id_catalogo": self.id_catalogo,
            "id_producto": self.id_producto,
            "orden": self.orden,
            "producto": self.producto.to_dict() if self.producto else None
        }


class Pedido(db.Model):
    __tablename__ = "pedidos"
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False, default=0.0)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')  # pendiente, confirmado, preparando, enviado, entregado, cancelado
    direccion_entrega = db.Column(db.String(255), nullable=False)
    telefono_contacto = db.Column(db.String(20), nullable=False)
    notas = db.Column(db.Text, nullable=True)
    fecha_entrega = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario = db.relationship('Usuario', back_populates='pedidos')
    detalles = db.relationship('DetallePedido', back_populates='pedido', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id_pedido": self.id_pedido,
            "id_usuario": self.id_usuario,
            "nombre_usuario": self.usuario.nombre if self.usuario else None,
            "fecha_pedido": self.fecha_pedido.strftime("%d/%m/%Y %H:%M") if self.fecha_pedido else None,
            "total": self.total,
            "estado": self.estado,
            "direccion_entrega": self.direccion_entrega,
            "telefono_contacto": self.telefono_contacto,
            "notas": self.notas,
            "fecha_entrega": self.fecha_entrega.strftime("%d/%m/%Y %H:%M") if self.fecha_entrega else None,
            "detalles": [d.to_dict() for d in self.detalles] if self.detalles else []
        }


class DetallePedido(db.Model):
    __tablename__ = "detalle_pedidos"
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id_pedido'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pedido = db.relationship('Pedido', back_populates='detalles')
    producto = db.relationship('Producto', back_populates='detalle_pedidos')
    
    def to_dict(self):
        return {
            "id_detalle": self.id_detalle,
            "id_pedido": self.id_pedido,
            "id_producto": self.id_producto,
            "producto": self.producto.producto if self.producto else None,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal
        }


class Favorito(db.Model):
    __tablename__ = "favoritos"
    id_favorito = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', back_populates='favoritos')
    producto = db.relationship('Producto', back_populates='favoritos')
    
    def to_dict(self):
        return {
            "id_favorito": self.id_favorito,
            "id_usuario": self.id_usuario,
            "id_producto": self.id_producto,
            "producto": self.producto.to_dict() if self.producto else None,
            "fecha_agregado": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else None
        }


class Carrito(db.Model):
    __tablename__ = "carritos"
    id_carrito = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False, unique=True)
    total = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario = db.relationship('Usuario', back_populates='carrito')
    items = db.relationship('CarritoItem', back_populates='carrito', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id_carrito": self.id_carrito,
            "id_usuario": self.id_usuario,
            "total": self.total,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "cantidad_items": sum(item.cantidad for item in self.items) if self.items else 0
        }


class CarritoItem(db.Model):
    __tablename__ = "carrito_items"
    id_item = db.Column(db.Integer, primary_key=True)
    id_carrito = db.Column(db.Integer, db.ForeignKey('carritos.id_carrito'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    carrito = db.relationship('Carrito', back_populates='items')
    producto = db.relationship('Producto', back_populates='carrito_items')
    
    def to_dict(self):
        return {
            "id_item": self.id_item,
            "id_carrito": self.id_carrito,
            "id_producto": self.id_producto,
            "producto": self.producto.producto if self.producto else None,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal
        }