from app.admin import administrador_bp
from flask import redirect, request, url_for, jsonify, render_template, flash, current_app, Response
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, bcrypt
from app.models import Usuario, Producto, Imagen, Categoria, Pedido, DetallePedido
from app.utils import save_image, delete_image, get_image_url
from datetime import date, datetime
import csv
import io

@administrador_bp.route("/")
@login_required
def dashboard():
    productos = Producto.query.all()
    categorias = Categoria.query.all()
    usuarios = Usuario.query.all()
    pedidos = Pedido.query.order_by(Pedido.fecha_pedido.desc()).all()
    
    for categoria in categorias:
        categoria.total_productos = len(categoria.productos)
    
    return render_template("admin/administracion.html", 
                         productos=productos, 
                         categorias=categorias,
                         usuarios=usuarios,
                         pedidos=pedidos,
                         total_productos=len(productos),
                         total_categorias=len(categorias),
                         total_usuarios=len(usuarios),
                         total_pedidos=len(pedidos))

# ============================================================
# GESTIÓN DE PEDIDOS
# ============================================================

@administrador_bp.route("/pedido/actualizar/<int:id_pedido>", methods=["POST"])
@login_required
def actualizar_estado_pedido(id_pedido):
    """Actualizar el estado de un pedido"""
    pedido = Pedido.query.get_or_404(id_pedido)
    nuevo_estado = request.form.get("estado")
    
    estados_validos = ['pendiente', 'confirmado', 'preparando', 'enviado', 'entregado', 'cancelado']
    
    if nuevo_estado not in estados_validos:
        return jsonify({"success": False, "message": "Estado no válido"}), 400
    
    try:
        pedido.estado = nuevo_estado
        if nuevo_estado == 'entregado':
            pedido.fecha_entrega = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Pedido actualizado a {nuevo_estado}",
            "nuevo_estado": nuevo_estado
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@administrador_bp.route("/pedido/detalle/<int:id_pedido>")
@login_required
def detalle_pedido(id_pedido):
    """Obtener detalles de un pedido (API)"""
    pedido = Pedido.query.get_or_404(id_pedido)
    return jsonify({
        "success": True,
        "pedido": pedido.to_dict()
    })

@administrador_bp.route("/api/pedidos")
@login_required
def api_listar_pedidos():
    """API para listar pedidos con filtros"""
    estado = request.args.get('estado', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    
    query = Pedido.query
    
    if estado and estado != 'todos':
        query = query.filter_by(estado=estado)
    if fecha_inicio:
        query = query.filter(Pedido.fecha_pedido >= datetime.strptime(fecha_inicio, '%Y-%m-%d'))
    if fecha_fin:
        query = query.filter(Pedido.fecha_pedido <= datetime.strptime(fecha_fin, '%Y-%m-%d'))
    
    pedidos = query.order_by(Pedido.fecha_pedido.desc()).all()
    
    return jsonify({
        "success": True,
        "pedidos": [p.to_dict() for p in pedidos]
    })

@administrador_bp.route("/exportar/pedidos")
@login_required
def exportar_pedidos_excel():
    """Exportar pedidos a CSV con formato Excel"""
    estado = request.args.get('estado', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    
    query = Pedido.query
    
    if estado and estado != 'todos':
        query = query.filter_by(estado=estado)
    if fecha_inicio:
        query = query.filter(Pedido.fecha_pedido >= datetime.strptime(fecha_inicio, '%Y-%m-%d'))
    if fecha_fin:
        query = query.filter(Pedido.fecha_pedido <= datetime.strptime(fecha_fin, '%Y-%m-%d'))
    
    pedidos = query.order_by(Pedido.fecha_pedido.desc()).all()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Encabezados
    writer.writerow([
        'ID Pedido', 'Cliente', 'Fecha Pedido', 'Total (Bs)', 'Estado', 
        'Direccion Entrega', 'Telefono Contacto', 'Notas', 'Fecha Entrega'
    ])
    
    # Datos
    for p in pedidos:
        writer.writerow([
            p.id_pedido,
            p.usuario.nombre if p.usuario else 'N/A',
            p.fecha_pedido.strftime('%d/%m/%Y %H:%M') if p.fecha_pedido else '',
            f"{p.total:.2f}",
            p.estado,
            p.direccion_entrega,
            p.telefono_contacto,
            p.notas or '',
            p.fecha_entrega.strftime('%d/%m/%Y %H:%M') if p.fecha_entrega else ''
        ])
    
    # Resumen
    writer.writerow([])
    writer.writerow(['RESUMEN DE PEDIDOS'])
    writer.writerow([f'Total Pedidos: {len(pedidos)}'])
    
    estados = ['pendiente', 'confirmado', 'preparando', 'enviado', 'entregado', 'cancelado']
    for estado_nombre in estados:
        count = sum(1 for p in pedidos if p.estado == estado_nombre)
        writer.writerow([f'{estado_nombre.capitalize()}: {count}'])
    
    total = sum(p.total for p in pedidos)
    writer.writerow([f'Total Recaudado: Bs {total:.2f}'])
    
    # Crear respuesta
    output.seek(0)
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=pedidos_{date.today().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

@administrador_bp.route("/exportar/productos")
@login_required
def exportar_productos_excel():
    """Exportar productos a CSV con formato Excel"""
    productos = Producto.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    
    writer.writerow([
        'ID Producto', 'Producto', 'Categoria', 'Precio (Bs)', 'Stock', 'Descripcion', 'ID Usuario'
    ])
    
    for p in productos:
        writer.writerow([
            p.id_producto,
            p.producto,
            p.categoria.categoria if p.categoria else 'Sin categoría',
            f"{p.precio:.2f}",
            p.stock,
            p.descripcion,
            p.id_usuario
        ])
    
    writer.writerow([])
    writer.writerow(['RESUMEN DE PRODUCTOS'])
    writer.writerow([f'Total Productos: {len(productos)}'])
    
    categorias = Categoria.query.all()
    for c in categorias:
        count = sum(1 for p in productos if p.id_categoria == c.id_categoria)
        if count > 0:
            writer.writerow([f'{c.categoria}: {count} productos'])
    
    output.seek(0)
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=productos_{date.today().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

@administrador_bp.route("/productos")
@login_required
def listar_productos():
    return redirect(url_for("admin.dashboard"))


@administrador_bp.route("/producto/crear", methods=["GET", "POST"])
@login_required
def crear_producto():
    if request.method == "POST":
        producto = request.form.get("producto")
        precio = request.form.get("precio")
        stock = request.form.get("stock")
        descripcion = request.form.get("descripcion")
        id_categoria = request.form.get("id_categoria")
        if not all([producto, precio, stock, descripcion, id_categoria]):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("admin.crear_producto")) 
        nuevo_producto = Producto(producto=producto,precio=float(precio),stock=int(stock),descripcion=descripcion,id_usuario=current_user.id_usuario,id_categoria=int(id_categoria))
        db.session.add(nuevo_producto)
        db.session.commit()
        
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                success, filename, message = save_image(file)
                if success:
                    nueva_imagen = Imagen(imagen=filename,id_producto=nuevo_producto.id_producto)
                    db.session.add(nueva_imagen)
                    db.session.commit()
                    flash("Producto creado con imagen exitosamente.", "success")
                else:
                    flash(f"Producto creado pero hubo un problema con la imagen: {message}", "warning")
            else:
                flash("Producto creado exitosamente (sin imagen).", "success")
        else:
            flash("Producto creado exitosamente.", "success")
        return redirect(url_for("admin.dashboard"))
            
    categorias = Categoria.query.all()
    return render_template("admin/producto_crear.html", categorias=categorias)


@administrador_bp.route("/producto/editar/<int:id_producto>", methods=["GET", "POST"])
@login_required
def editar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    if producto.id_usuario != current_user.id_usuario:
        flash("No tienes permiso para editar este producto.", "error")
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        producto.producto = request.form.get("producto")
        producto.precio = float(request.form.get("precio"))
        producto.stock = int(request.form.get("stock"))
        producto.descripcion = request.form.get("descripcion")
        producto.id_categoria = int(request.form.get("id_categoria"))

        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                if producto.imagenes:
                    for img in producto.imagenes:
                        delete_image(img.imagen)
                        db.session.delete(img)
                success, filename, message = save_image(file)
                if success:
                    nueva_imagen = Imagen(imagen=filename,id_producto=producto.id_producto)
                    db.session.add(nueva_imagen)
                    flash("Producto actualizado con nueva imagen.", "success")
                else:
                    flash(f"Producto actualizado pero hubo un problema con la imagen: {message}", "warning")
        db.session.commit()
        flash("Producto actualizado exitosamente.", "success")
        return redirect(url_for("admin.dashboard"))
    categorias = Categoria.query.all()
    return render_template("admin/producto_editar.html", producto=producto, categorias=categorias)


@administrador_bp.route("/producto/eliminar/<int:id_producto>", methods=["POST"])
@login_required
def eliminar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    if producto.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No tienes permiso para eliminar este producto."}), 403
    for imagen in producto.imagenes:
        delete_image(imagen.imagen)
    
    db.session.delete(producto)
    db.session.commit()
    return jsonify({"success": True, "message": "Producto eliminado exitosamente."})


@administrador_bp.route("/producto/ver/<int:id_producto>")
@login_required
def ver_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    return render_template("admin/producto_ver.html", producto=producto)


@administrador_bp.route("/categorias")
@login_required
def listar_categorias():
    return redirect(url_for("admin.dashboard"))


@administrador_bp.route("/categoria/crear", methods=["POST"])
@login_required
def crear_categoria():
    categoria = request.form.get("categoria")
    
    if not categoria:
        return jsonify({"success": False, "message": "El nombre de la categoría es obligatorio."}), 400
    
    existe = Categoria.query.filter_by(categoria=categoria).first()
    if existe:
        return jsonify({"success": False, "message": "La categoría ya existe."}), 400
    
    nueva_categoria = Categoria(categoria=categoria)
    db.session.add(nueva_categoria)
    db.session.commit()
    return jsonify({
        "success": True, 
        "message": "Categoría creada exitosamente.",
        "categoria": nueva_categoria.to_dict()
    })


@administrador_bp.route("/categoria/editar/<int:id_categoria>", methods=["PUT", "POST"])
@login_required
def editar_categoria(id_categoria):
    categoria = Categoria.query.get_or_404(id_categoria)
    nuevo_nombre = request.form.get("categoria") if request.method == "POST" else request.get_json().get("categoria")
    if not nuevo_nombre:
        return jsonify({"success": False, "message": "El nombre de la categoría es obligatorio."}), 400
    existe = Categoria.query.filter_by(categoria=nuevo_nombre).first()
    if existe and existe.id_categoria != id_categoria:
        return jsonify({"success": False, "message": "Ya existe una categoría con ese nombre."}), 400
    categoria.categoria = nuevo_nombre
    db.session.commit()
    return jsonify({
        "success": True, 
        "message": "Categoría actualizada exitosamente.",
        "categoria": categoria.to_dict()
    })


@administrador_bp.route("/categoria/eliminar/<int:id_categoria>", methods=["DELETE", "POST"])
@login_required
def eliminar_categoria(id_categoria):
    categoria = Categoria.query.get_or_404(id_categoria)
    if categoria.productos:
        return jsonify({
            "success": False, 
            "message": "No se puede eliminar la categoría porque tiene productos asociados."
        }), 400

    db.session.delete(categoria)
    db.session.commit()
    return jsonify({"success": True, "message": "Categoría eliminada exitosamente."})


@administrador_bp.route("/imagen/crear", methods=["POST"])
@login_required
def crear_imagen():
    id_producto = request.form.get("id_producto")
    if not id_producto:
        return jsonify({"success": False, "message": "ID de producto es obligatorio."}), 400
    producto = Producto.query.get_or_404(id_producto)
    if producto.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No tienes permiso para agregar imágenes a este producto."}), 403
    if 'imagen' not in request.files:
        return jsonify({"success": False, "message": "No se seleccionó ningún archivo."}), 400
    file = request.files['imagen']
    if file.filename == '':
        return jsonify({"success": False, "message": "No se seleccionó ningún archivo."}), 400
    success, filename, message = save_image(file)
    if not success:
        return jsonify({"success": False, "message": message}), 400
    nueva_imagen = Imagen(imagen=filename,id_producto=int(id_producto))
    db.session.add(nueva_imagen)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Imagen agregada exitosamente.",
        "imagen": nueva_imagen.to_dict(),
        "url": get_image_url(filename)
    })


@administrador_bp.route("/imagen/eliminar/<int:id_imagen>", methods=["DELETE", "POST"])
@login_required
def eliminar_imagen(id_imagen):
    imagen = Imagen.query.get_or_404(id_imagen)
    if imagen.producto.id_usuario != current_user.id_usuario:
        return jsonify({"success": False, "message": "No tienes permiso para eliminar esta imagen."}), 403
    delete_image(imagen.imagen)
    db.session.delete(imagen)
    db.session.commit()
    return jsonify({"success": True, "message": "Imagen eliminada exitosamente."})

@administrador_bp.route("/usuarios")
@login_required
def listar_usuarios():
    if current_user.rol.lower() not in ["admin", "administrador"]:
        flash("Acceso denegado.", "error")
        return redirect(url_for("main.index"))
    usuarios = Usuario.query.all()
    return render_template("admin/usuarios.html", usuarios=usuarios,total_usuarios=len(usuarios))

@administrador_bp.route("/usuario/ver/<int:id_usuario>")
@login_required
def ver_usuario(id_usuario):
    if current_user.rol.lower() not in ["admin", "administrador"]:
        return jsonify({"success": False, "message": "Acceso denegado."}), 403
    usuario = Usuario.query.get_or_404(id_usuario)
    return jsonify({
        "success": True,
        "usuario": usuario.to_dict()
    })


@administrador_bp.route("/usuario/editar/<int:id_usuario>", methods=["POST"])
@login_required
def editar_usuario(id_usuario):
    if current_user.rol.lower() not in ["admin", "administrador"]:
        return jsonify({"success": False, "message": "Acceso denegado."}), 403
    usuario = Usuario.query.get_or_404(id_usuario)
    if usuario.id_usuario == current_user.id_usuario:
        return jsonify({"success": False, "message": "No puedes editarte a ti mismo."}), 400
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    telefono = request.form.get("telefono")
    rol = request.form.get("rol")
    if not all([nombre, email, telefono, rol]):
        return jsonify({"success": False, "message": "Todos los campos son obligatorios."}), 400
    existe = Usuario.query.filter_by(email=email).first()
    if existe and existe.id_usuario != id_usuario:
        return jsonify({"success": False, "message": "El email ya está registrado."}), 400
    usuario.nombre = nombre
    usuario.email = email
    usuario.telefono = telefono
    usuario.rol = rol.lower()
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Usuario actualizado exitosamente.",
        "usuario": usuario.to_dict()
    })

@administrador_bp.route("/usuario/eliminar/<int:id_usuario>", methods=["DELETE", "POST"])
@login_required
def eliminar_usuario(id_usuario):
    if current_user.rol.lower() not in ["admin", "administrador"]:
        return jsonify({"success": False, "message": "Acceso denegado."}), 403
    usuario = Usuario.query.get_or_404(id_usuario)
    if usuario.id_usuario == current_user.id_usuario:
        return jsonify({"success": False, "message": "No puedes eliminarte a ti mismo."}), 400
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"success": True, "message": "Usuario eliminado exitosamente."})


@administrador_bp.route("/usuario/productos/<int:id_usuario>")
@login_required
def listar_productos_usuario(id_usuario):
    if current_user.rol.lower() not in ["admin", "administrador"]:
        flash("Acceso denegado.", "error")
        return redirect(url_for("main.index"))
    usuario = Usuario.query.get_or_404(id_usuario)
    productos = Producto.query.filter_by(id_usuario=id_usuario).all()
    return render_template("admin/usuario_productos.html", usuario=usuario, productos=productos)


@administrador_bp.route("/api/productos")
@login_required
def api_listar_productos():
    productos = Producto.query.all()
    productos_data = []
    for p in productos:
        data = p.to_dict()
        if p.imagenes:
            data['imagenes'] = [{
                'id': img.id_imagen,
                'url': get_image_url(img.imagen),
                'filename': img.imagen
            } for img in p.imagenes]
        productos_data.append(data)
    return jsonify({
        "success": True,
        "productos": productos_data
    })


@administrador_bp.route("/api/producto/<int:id_producto>")
@login_required
def api_ver_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    data = producto.to_dict()
    if producto.imagenes:
        data['imagenes'] = [{
            'id': img.id_imagen,
            'url': get_image_url(img.imagen),
            'filename': img.imagen
        } for img in producto.imagenes]
    return jsonify({
        "success": True,
        "producto": data
    })


@administrador_bp.route("/api/categorias")
@login_required
def api_listar_categorias():
    categorias = Categoria.query.all()
    return jsonify({
        "success": True,
        "categorias": [c.to_dict() for c in categorias]
    })

@administrador_bp.route("/perfil")
@login_required
def perfil():
    return render_template("admin/perfil.html", usuario=current_user)

@administrador_bp.route("/reportes")
@login_required
def reportes():
    return render_template("admin/reportes.html")

@administrador_bp.route("/api/perfil/actualizar", methods=["POST"])
@login_required
def api_actualizar_perfil():
    data = request.get_json() or {}
    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip()
    telefono = data.get("telefono", "").strip()

    if not nombre or not email or not telefono:
        return jsonify({"success": False, "message": "Todos los campos obligatorios (*)"}), 400

    email_existente = Usuario.query.filter(Usuario.email == email, Usuario.id_usuario != current_user.id_usuario).first()
    if email_existente:
        return jsonify({"success": False, "message": "Este correo electrónico ya está en uso."}), 400

    try:
        current_user.nombre = nombre
        current_user.email = email
        current_user.telefono = telefono
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": "Datos de perfil actualizados correctamente.",
            "usuario": current_user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)}"}), 500


@administrador_bp.route("/api/perfil/cambiar-password", methods=["POST"])
@login_required
def api_cambiar_password():
    data = request.get_json() or {}
    password_actual = data.get("password_actual", "")
    password_nueva = data.get("password_nueva", "")
    password_confirmar = data.get("password_confirmar", "")

    if not password_actual or not password_nueva or not password_confirmar:
        return jsonify({"success": False, "message": "Todos los campos de contraseña son requeridos."}), 400
    if password_nueva != password_confirmar:
        return jsonify({"success": False, "message": "La nueva contraseña y su confirmación no coinciden."}), 400
    if len(password_nueva) < 8:
        return jsonify({"success": False, "message": "La nueva contraseña debe tener al menos 8 caracteres."}), 400

    if not bcrypt.check_password_hash(current_user.password, password_actual):
        return jsonify({"success": False, "message": "La contraseña actual es incorrecta."}), 401

    try:
        password_hash = bcrypt.generate_password_hash(password_nueva).decode('utf-8')
        current_user.password = password_hash
        db.session.commit()
        return jsonify({"success": True, "message": "Contraseña actualizada con éxito."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al cambiar contraseña: {str(e)}"}), 500

@administrador_bp.route("/api/reportes/estadisticas")
@login_required
def api_reportes_estadisticas():
    try:
        query_busqueda = request.args.get('q', '').strip()

        consulta_criticos = Producto.query.filter(Producto.stock <= 10)
        
        if query_busqueda:
            consulta_criticos = consulta_criticos.filter(Producto.producto.ilike(f"%{query_busqueda}%"))
            
        criticos = consulta_criticos.all()
        
        alertas_stock = []
        for p in criticos:
            nombre_cat = "General"
            if p.categoria:
                nombre_cat = p.categoria.categoria

            alertas_stock.append({
                "id_producto": p.id_producto,
                "producto": p.producto,
                "stock": p.stock,
                "precio": p.precio,
                "categoria": nombre_cat
            })

        categorias = Categoria.query.all()
        datos_categorias = []
        for c in categorias:
            datos_categorias.append({
                "categoria": c.categoria,
                "total_productos": len(c.productos) if c.productos else 0
            })

        total_productos_sistema = Producto.query.count() or 0
        total_categorias_sistema = Categoria.query.count() or 0
        
        total_existencias_fisicas = 0
        todos_los_productos = Producto.query.all()
        for prod in todos_los_productos:
            if prod.stock:
                total_existencias_fisicas += int(prod.stock)

        return jsonify({
            "success": True,
            "alertas_stock": alertas_stock,
            "total_alertas": len(alertas_stock),
            "categorias_estadistica": datos_categorias,
            "catalogo_kpis": {
                "total_productos": total_productos_sistema,
                "total_categorias": total_categorias_sistema,
                "total_stock_fisico": total_existencias_fisicas
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error interno en la consulta: {str(e)}"}), 500
    

