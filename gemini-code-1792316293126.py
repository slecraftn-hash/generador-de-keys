import json
import urllib.parse
import urllib.request
import urllib.error
import secrets
from datetime import datetime, timedelta
from functools import wraps
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Tus datos de la API actualizados
API_BASE = "http://69.197.142.47:10043"
ADMIN_API_KEY = "Paloq!gg"

# Token de tu bot
TOKEN = "8998224860:AAHCxlM3GKXvrG7rgw_ZIpyfTR-44Of-9gk"

# Tu ID de Telegram verificado (Exclusivo para Admin)
ADMIN_IDS = [8046948909]

# Diccionario donde guardaremos a los usuarios autorizados con su fecha de expiración: {"username": fecha_limite}
USUARIOS_AUTORIZADOS = {} 

def restricted(func):
    """Decorador para permitir el acceso solo al admin principal o usuarios con membresía vigente"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # El admin principal siempre tiene acceso
        if user_id in ADMIN_IDS:
            return await func(update, context)
            
        # Verificar si el usuario tiene un username válido y está en la lista
        if username:
            clean_username = username.lower()
            if clean_username in USUARIOS_AUTORIZADOS:
                # Comprobar si la membresía sigue vigente
                fecha_expiracion = USUARIOS_AUTORIZADOS[clean_username]
                if datetime.now() < fecha_expiracion:
                    return await func(update, context)
                else:
                    # Si ya expiró, lo eliminamos automáticamente
                    del USUARIOS_AUTORIZADOS[clean_username]
        
        await update.message.reply_text("⛔ **Acceso denegado o membresía expirada.** No tienes autorización vigente para usar este bot.")
        return
    return wrapper

def admin_only(func):
    """Decorador exclusivo para que SOLO el administrador principal pueda usar el comando"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in ADMIN_IDS:
            return await func(update, context)
        
        await update.message.reply_text("⛔ **Comando restringido.** Solo el administrador puede usar esta función.")
        return
    return wrapper

def llamar_api(endpoint, params=None):
    """Hace la petición a la API evitando codificar de más la clave"""
    url = f"{API_BASE}/{ADMIN_API_KEY}/{endpoint}"
    
    if params:
        query = urllib.parse.urlencode(params)
        url += f"?{query}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read().decode('utf-8')
            return True, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return False, f"Error HTTP {e.code}: {body}"
    except Exception as e:
        return False, f"Error de conexión: {e}"

@restricted
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú público para usuarios autorizados"""
    texto_menu = (
        "🤖 **MENÚ DE GESTIÓN DE KEYS** 🤖\n\n"
        "Comandos disponibles:\n\n"
        "• `/generar` [días]\n"
        "  _Genera una key individual (Ej: /generar 30)_\n\n"
        "• `/lote` [nombre] [cantidad] [días]\n"
        "  _Genera múltiples keys (Ej: /lote file1 5 30)_\n\n"
        "• `/comprobar` [key]\n"
        "  _Revisa el estado de una key_\n\n"
        "• `/eliminar` [key]\n"
        "  _Borra una key_\n\n"
        "• `/menu`\n"
        "  _Muestra este menú_"
    )
    await update.message.reply_text(texto_menu, parse_mode="Markdown")

@admin_only
async def menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú exclusivo y privado para el administrador"""
    texto_admin = (
        "👑 **MENÚ DE ADMINISTRACIÓN EXCLUSIVO** 👑\n\n"
        "Comandos de control:\n\n"
        "• `/agregar` [username] [días]\n"
        "  _Da acceso temporal a un usuario (Ej: /agregar juanito 7)_\n\n"
        "• `/borrar_todos`\n"
        "  _Elimina todos los usuarios autorizados de la lista_\n\n"
        "• `/menuadmin`\n"
        "  _Muestra este panel de administración_"
    )
    await update.message.reply_text(texto_admin, parse_mode="Markdown")

@admin_only
async def agregar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando exclusivo del administrador para agregar usuarios con límite de tiempo"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Uso correcto: `/agregar` [username] [días]\nEjemplo: `/agregar juanito 7`", parse_mode="Markdown")
        return
    
    nuevo_user = args[0].replace("@", "").strip().lower()
    try:
        dias = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Los días deben ser un número entero. Ejemplo: `/agregar juanito 7`", parse_mode="Markdown")
        return
    
    fecha_expiracion = datetime.now() + timedelta(days=dias)
    USUARIOS_AUTORIZADOS[nuevo_user] = fecha_expiracion
    
    fecha_formateada = fecha_expiracion.strftime('%d/%m/%Y %H:%M')
    await update.message.reply_text(
        f"✅ ¡Usuario **@{nuevo_user}** autorizado por **{dias} días**!\n"
        f"⏳ Válido hasta: `{fecha_formateada}`", 
        parse_mode="Markdown"
    )

@admin_only
async def borrar_todos_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando exclusivo del administrador para vaciar la lista de usuarios autorizados"""
    USUARIOS_AUTORIZADOS.clear()
    await update.message.reply_text
