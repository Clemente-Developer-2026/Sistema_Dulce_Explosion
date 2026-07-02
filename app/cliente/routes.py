from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.cliente import cliente_bp
from app.extensions import db
from app.models import Producto, Categoria, Imagen, Favorito, Carrito, CarritoItem, Catalogo, CatalogoProducto, Pedido, DetallePedido
from app.utils import get_image_url
from sqlalchemy import desc
from datetime import datetime

@cliente_bp.route("/")
@login_required
def catalogo():
    if current_user.rol.lower() in ["admin", "administrador"]:
        flash("Los administradores deben usar el panel de administración.", "info")
        return redirect(url_for("admin.dashboard"))
    productos = Producto.query.filter(Producto.stock > 0).all()
    categorias = Categoria.query.all()
    catalogos_activos = Catalogo.query.filter(
        Catalogo.activo == True,
        Catalogo.fecha_inicio <= datetime.utcnow()).filter((Catalogo.fecha_fin >= datetime.utcnow()) | (Catalogo.fecha_fin.is_(None))).all()
    productos_destacados = []
    for catalogo in catalogos_activos:
        for cp in catalogo.productos:
            if cp.producto.stock > 0:
                productos_destacados.append(cp.producto)
    
    productos_destacados = list(dict.fromkeys(productos_destacados))
    
    favoritos_ids = []
    if current_user.is_authenticated:
        favoritos = Favorito.query.filter_by(id_usuario=current_user.id_usuario).all()
        favoritos_ids = [f.id_producto for f in favoritos]
    
    # Obtener carrito para el contador
    carrito = Carrito.query.filter_by(id_usuario=current_user.id_usuario).first()
    cantidad_carrito = sum(item.cantidad for item in carrito.items) if carrito else 0
    
    return render_template("cliente/catalogo.html",productos=productos,categorias=categorias,productos_destacados=productos_destacados[:8],favoritos_ids=favoritos_ids,cantidad_carrito=cantidad_carrito,get_image_url=get_image_url)


@cliente_bp.route("/producto/<int:id_producto>")
@login_required
def detalle_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    
    if producto.stock <= 0:
        flash("Este producto no está disponible actualmente.", "warning")
        return redirect(url_for("cliente.catalogo"))
    
    es_favorito = False
    if current_user.is_authenticated:
        es_favorito = Favorito.query.filter_by(
            id_usuario=current_user.id_usuario,
            id_producto=id_producto
        ).first() is not None
    
    productos_relacionados = Producto.query.filter(
        Producto.id_categoria == producto.id_categoria,
        Producto.id_producto != id_producto,
        Producto.stock > 0
    ).limit(4).all()
    
    return render_template("cliente/detalle_producto.html",producto=producto,es_favorito=es_favorito,productos_relacionados=productos_relacionados,get_image_url=get_image_url)


@cliente_bp.route("/favoritos/toggle/<int:id_producto>", methods=["POST"])
@login_required
def toggle_favorito(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    favorito = Favorito.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_producto=id_producto
    ).first()
    
    if favorito:
        db.session.delete(favorito)
        db.session.commit()
        return jsonify({"success": True, "action": "removed", "message": "Producto eliminado de favoritos"})
    else:
        nuevo_favorito = Favorito(
            id_usuario=current_user.id_usuario,
            id_producto=id_producto
        )
        db.session.add(nuevo_favorito)
        db.session.commit()
        return jsonify({"success": True, "action": "added", "message": "Producto agregado a favoritos"})


@cliente_bp.route("/favoritos")
@login_required
def favoritos():
    favoritos = Favorito.query.filter_by(id_usuario=current_user.id_usuario).all()
    productos = [f.producto for f in favoritos if f.producto.stock > 0]
    return render_template("cliente/favoritos.html",productos=productos,get_image_url=get_image_url)


@cliente_bp.route("/mispedidos")
@login_required
def mispedidos():
    pedidos = Pedido.query.filter_by(id_usuario=current_user.id_usuario).order_by(Pedido.fecha_pedido.desc()).all()
    return render_template("cliente/mispedidos.html", pedidos=pedidos, get_image_url=get_image_url)


@cliente_bp.route("/pedido/detalle/<int:id_pedido>")
@login_required
def detalle_pedido(id_pedido):
    pedido = Pedido.query.get_or_404(id_pedido)
    if pedido.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No autorizado"}), 403
    return jsonify({
        "success": True,
        "pedido": pedido.to_dict()
    })


@cliente_bp.route("/carrito")
@login_required
def carrito():
    carrito = Carrito.query.filter_by(id_usuario=current_user.id_usuario).first()
    if not carrito:
        carrito = Carrito(id_usuario=current_user.id_usuario, total=0)
        db.session.add(carrito)
        db.session.commit()
    return render_template("cliente/carrito.html",carrito=carrito,get_image_url=get_image_url)


@cliente_bp.route("/carrito/agregar/<int:id_producto>", methods=["POST"])
@login_required
def agregar_carrito(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    cantidad = int(request.form.get("cantidad", 1))
    
    if producto.stock < cantidad:
        return jsonify({"success": False, "message": "No hay suficiente stock disponible"}), 400
    carrito = Carrito.query.filter_by(id_usuario=current_user.id_usuario).first()
    if not carrito:
        carrito = Carrito(id_usuario=current_user.id_usuario, total=0)
        db.session.add(carrito)
        db.session.commit()
    
    item = CarritoItem.query.filter_by(
        id_carrito=carrito.id_carrito,
        id_producto=id_producto
    ).first()
    
    if item:
        nueva_cantidad = item.cantidad + cantidad
        if producto.stock < nueva_cantidad:
            return jsonify({"success": False, "message": "No hay suficiente stock disponible"}), 400
        item.cantidad = nueva_cantidad
        item.subtotal = item.cantidad * item.precio_unitario
    else:
        item = CarritoItem(
            id_carrito=carrito.id_carrito,
            id_producto=id_producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            subtotal=producto.precio * cantidad
        )
        db.session.add(item)
    carrito.total = sum(i.subtotal for i in carrito.items)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Producto agregado al carrito",
        "total": carrito.total,
        "cantidad_items": sum(i.cantidad for i in carrito.items)
    })


@cliente_bp.route("/carrito/eliminar/<int:id_item>", methods=["POST"])
@login_required
def eliminar_carrito(id_item):
    item = CarritoItem.query.get_or_404(id_item)
    
    if item.carrito.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No autorizado"}), 403
    
    db.session.delete(item)
    carrito = item.carrito
    carrito.total = sum(i.subtotal for i in carrito.items)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Producto eliminado del carrito",
        "total": carrito.total,
        "cantidad_items": sum(i.cantidad for i in carrito.items)
    })


@cliente_bp.route("/carrito/actualizar/<int:id_item>", methods=["POST"])
@login_required
def actualizar_carrito(id_item):
    item = CarritoItem.query.get_or_404(id_item)
    cantidad = int(request.form.get("cantidad", 1))
    if item.carrito.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No autorizado"}), 403
    producto = Producto.query.get(item.id_producto)
    if producto.stock < cantidad:
        return jsonify({"success": False, "message": "No hay suficiente stock"}), 400
    if cantidad <= 0:
        db.session.delete(item)
    else:
        item.cantidad = cantidad
        item.subtotal = cantidad * item.precio_unitario
    carrito = item.carrito
    carrito.total = sum(i.subtotal for i in carrito.items)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Carrito actualizado",
        "total": carrito.total,
        "cantidad_items": sum(i.cantidad for i in carrito.items)
    })


@cliente_bp.route("/carrito/finalizar", methods=["POST"])
@login_required
def finalizar_pedido():
    carrito = Carrito.query.filter_by(id_usuario=current_user.id_usuario).first()
    if not carrito or not carrito.items:
        return jsonify({"success": False, "message": "El carrito está vacío"}), 400
    data = request.get_json()
    direccion_entrega = data.get("direccion_entrega")
    telefono_contacto = data.get("telefono_contacto")
    notas = data.get("notas", "")
    if not direccion_entrega or not telefono_contacto:
        return jsonify({"success": False, "message": "Dirección y teléfono son obligatorios"}), 400
    try:
        pedido = Pedido(
            id_usuario=current_user.id_usuario,
            total=carrito.total,
            direccion_entrega=direccion_entrega,
            telefono_contacto=telefono_contacto,
            notas=notas,
            estado="pendiente"
        )
        db.session.add(pedido)
        db.session.flush()
        for item in carrito.items:
            detalle = DetallePedido(
                id_pedido=pedido.id_pedido,
                id_producto=item.id_producto,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal
            )
            db.session.add(detalle)
            producto = Producto.query.get(item.id_producto)
            producto.stock -= item.cantidad
        for item in carrito.items:
            db.session.delete(item)
        carrito.total = 0
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Pedido realizado exitosamente",
            "pedido_id": pedido.id_pedido
        })   
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al procesar el pedido: {str(e)}"}), 500
    
@cliente_bp.route("/perfil")
@login_required
def perfil():
    return render_template("cliente/perfil.html", usuario=current_user)

@cliente_bp.route("/api/productos")
@login_required
def api_productos():
    categoria = request.args.get("categoria")
    busqueda = request.args.get("busqueda", "").strip()
    query = Producto.query.filter(Producto.stock > 0)
    if categoria and categoria != "todos":
        query = query.filter_by(id_categoria=int(categoria))
    if busqueda:
        query = query.filter(Producto.producto.ilike(f"%{busqueda}%"))
    productos = query.all()
    productos_data = []
    for p in productos:
        data = p.to_dict()
        data["imagen"] = get_image_url(p.imagenes[0].imagen) if p.imagenes else None
        productos_data.append(data)
    return jsonify({
        "success": True,
        "productos": productos_data
    })


@cliente_bp.route("/api/categorias")
@login_required
def api_categorias():
    categorias = Categoria.query.all()
    return jsonify({
        "success": True,
        "categorias": [c.to_dict() for c in categorias]
    })

@cliente_bp.route("/api/carrito")
@login_required
def api_carrito():
    carrito = Carrito.query.filter_by(id_usuario=current_user.id_usuario).first()
    
    if not carrito:
        return jsonify({
            "success": True,
            "carrito": {
                "items": [],
                "total": 0,
                "cantidad_items": 0
            }
        })
    
    return jsonify({
        "success": True,
        "carrito": {
            "items": [item.to_dict() for item in carrito.items],
            "total": carrito.total,
            "cantidad_items": sum(item.cantidad for item in carrito.items)
        }
    })