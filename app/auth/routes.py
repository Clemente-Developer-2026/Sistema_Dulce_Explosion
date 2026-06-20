from flask import redirect, request, url_for, jsonify, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date
from app.extensions import db, bcrypt
from app.auth import usuarios_bp
from app.models import Usuario


@usuarios_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        password = request.form.get("password")
        rol = request.form.get("rol", "cliente")
        if not all([nombre, email, telefono, password]):
            flash("Todos los campos marcados con * son obligatorios.", "error")
            return redirect(url_for("auth.registro"))
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash("Este correo electrónico ya está registrado.", "error")
            return redirect(url_for("auth.registro"))
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        nuevo_usuario = Usuario(nombre=nombre,email=email,telefono=telefono,rol=rol.lower(), password=password_hash,fecha_registro=date.today())
        db.session.add(nuevo_usuario)
        db.session.commit()
        login_user(nuevo_usuario)
        if rol.lower() in ["admin", "administrador"]:
            flash(f"¡Bienvenido Administrador {nombre}!", "success")
            return redirect(url_for("main.administracion"))
        else:
            flash(f"¡Bienvenido {nombre}! Tu cuenta ha sido creada exitosamente.", "success")
            return redirect(url_for("main.pedidos"))               



@usuarios_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember") == "on"
        if not email or not password:
            flash("Por favor, ingresa tu email y contraseña.", "error")
            return redirect(url_for("auth.login"))
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            login_user(usuario, remember=remember)
            if usuario.rol.lower() in ["admin", "administrador"]:
                flash(f"¡Bienvenido Administrador {usuario.nombre}!", "success")
                return redirect(url_for("main.administracion"))
            else:
                flash(f"¡Bienvenido {usuario.nombre}!", "success")
                return redirect(url_for("main.pedidos"))
        else:
            flash("Credenciales incorrectas. Por favor, verifica tu email y contraseña.", "error")
            return redirect(url_for("auth.login"))
    return render_template("auth/login.html")


@usuarios_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("main.index"))


@usuarios_bp.route("/verificar_rol")
@login_required
def verificar_rol():
    if current_user.rol.lower() in ["admin", "administrador"]:
        return jsonify({
            "success": True,
            "rol": "administrador",
            "nombre": current_user.nombre,
            "email": current_user.email
        })
    else:
        return jsonify({
            "success": True,
            "rol": "cliente",
            "nombre": current_user.nombre,
            "email": current_user.email
        })


@usuarios_bp.route("/api/registro", methods=["POST"])
def api_registro():
    data = request.get_json()
    required_fields = ["nombre", "email", "telefono", "password"]
    if not all(field in data for field in required_fields):
        return jsonify({
            "success": False, 
            "message": "Todos los campos son requeridos"
        }), 400  
    nombre = data.get("nombre")
    email = data.get("email")
    telefono = data.get("telefono")
    password = data.get("password")
    rol = data.get("rol", "cliente")
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return jsonify({
            "success": False, 
            "message": "Este correo electrónico ya está registrado"
        }), 400
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    nuevo_usuario = Usuario(nombre=nombre,email=email,telefono=telefono,rol=rol.lower(),password=password_hash,fecha_registro=date.today())
    db.session.add(nuevo_usuario)
    db.session.commit()
    login_user(nuevo_usuario)
    if rol.lower() in ["admin", "administrador"]:
        redirect_url = url_for("main.administracion")
        tipo = "administrador"
    else:
        redirect_url = url_for("main.pedidos")
        tipo = "cliente"
    return jsonify({
        "success": True,
        "message": "Registro exitoso",
        "redirect": redirect_url,
        "usuario": {
            "id": nuevo_usuario.id_usuario,
            "nombre": nuevo_usuario.nombre,
            "email": nuevo_usuario.email,
            "rol": nuevo_usuario.rol,
            "tipo": tipo
        }
    })



@usuarios_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    remember = data.get("remember", False)
    if not email or not password:
        return jsonify({
            "success": False, 
            "message": "Email y contraseña son requeridos"
        }), 400
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario and bcrypt.check_password_hash(usuario.password, password):
        login_user(usuario, remember=remember)
        if usuario.rol.lower() in ["admin", "administrador"]:
            redirect_url = url_for("main.administracion")
            tipo = "administrador"
        else:
            redirect_url = url_for("main.pedidos")
            tipo = "cliente"    
        return jsonify({
            "success": True,
            "message": "Login exitoso",
            "redirect": redirect_url,
            "usuario": {
                "id": usuario.id_usuario,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "rol": usuario.rol,
                "tipo": tipo
            }
        })
    else:
        return jsonify({
            "success": False, 
            "message": "Credenciales incorrectas"
        }), 401


@usuarios_bp.route("/api/verificar-sesion")
def api_verificar_sesion():
    if current_user.is_authenticated:
        if current_user.rol.lower() in ["admin", "administrador"]:
            tipo = "administrador"
        else:
            tipo = "cliente"
            
        return jsonify({
            "authenticated": True,
            "usuario": {
                "id": current_user.id_usuario,
                "nombre": current_user.nombre,
                "email": current_user.email,
                "rol": current_user.rol,
                "tipo": tipo
            }
        })
    else:
        return jsonify({
            "authenticated": False
        })