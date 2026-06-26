from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.main import main_bp

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.rol.lower() in ["admin", "administrador"]:
            return redirect(url_for("admin.dashboard"))
        else:
            return redirect(url_for("cliente.catalogo"))  # ✅ Cliente va al catálogo
    return render_template("main/index.html")

@main_bp.route("/administracion")
@login_required
def administracion():
    if current_user.rol.lower() not in ["admin", "administrador"]:
        flash("Acceso denegado. Solo administradores pueden acceder a esta sección.", "error")
        return redirect(url_for("cliente.catalogo"))
    return redirect(url_for("admin.dashboard"))

@main_bp.route("/pedidos")
@login_required
def pedidos():
    """Redirige a la página de pedidos del cliente"""
    return redirect(url_for("cliente.mispedidos"))  # ✅ Cambiado a cliente.mispedidos

@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.rol.lower() in ["admin", "administrador"]:
        return redirect(url_for("admin.dashboard"))
    else:
        return redirect(url_for("cliente.mispedidos"))  # ✅ Cambiado a cliente.mispedidos

@main_bp.route("/perfil")
@login_required
def perfil():
    """Redirige al perfil del cliente"""
    return render_template("cliente/perfil.html", usuario=current_user)  # ✅ Ya apunta a cliente/perfil.html

@main_bp.route("/check-auth")
def check_auth():
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "usuario": {
                "id": current_user.id_usuario,
                "nombre": current_user.nombre,
                "email": current_user.email,
                "rol": current_user.rol
            }
        })
    else:
        return jsonify({"authenticated": False})

@main_bp.route("/check-role")
@login_required
def check_role():
    if current_user.rol.lower() in ["admin", "administrador"]:
        rol = "administrador"
    else:
        rol = "cliente"
    
    return jsonify({
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol,
        "tipo": rol,
        "es_administrador": current_user.rol.lower() in ["admin", "administrador"]
    })