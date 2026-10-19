import json
import urllib.parse
import urllib.request
import urllib.error
import secrets
from datetime import datetime, timedelta
from functools import wraps
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Tus datos de la API
API_BASE = "http://155.117.40.185:10068"
ADMIN_API_KEY = "Wen0PWx!loa"

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

def llamar_api(endpoint, params):
    """Hace la petición a la API y devuelve un diccionario con la respuesta JSON"""
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}/{urllib.parse.quote(ADMIN_API_KEY, safe='')}/{endpoint}"
    if query:
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
        "  _Genera múltiples keys (Ej: /lote casawa 5 30)_\n\n"
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
    
    # Calcular la fecha de expiración sumando los días actuales
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
    await update.message.reply_text("🗑️ **¡Lista vaciada!** Se han eliminado todos los usuarios autorizados del sistema.", parse_mode="Markdown")

@restricted
async def generar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    days = args[0] if args else "10"
    
    key_aleatoria = f"csw_{secrets.token_hex(4).upper()}"
    exito, res = llamar_api("generate", {"key": key_aleatoria, "days": days})
    
    if exito and isinstance(res, dict) and res.get("success"):
        mensaje = f"✅ **¡Key Generada!**\n\n🔑 `{key_aleatoria}`\n⏳ **Duración:** {days} días"
    else:
        mensaje = f"❌ **Error:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

@restricted
async def lote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Usa: `/lote` [nombre] [cantidad] [días]", parse_mode="Markdown")
        return
    
    name = args[0]
    try:
        count = int(args[1])
        days = args[2]
    except ValueError:
        await update.message.reply_text("⚠️ La cantidad debe ser un número entero.", parse_mode="Markdown")
        return

    if count > 30:
        await update.message.reply_text("⚠️ Máximo 30 keys por lote.", parse_mode="Markdown")
        return

    keys_generadas = []
    for _ in range(count):
        key_aleatoria = f"csw_{secrets.token_hex(4).upper()}"
        exito, res = llamar_api("generate", {"key": key_aleatoria, "days": days})
        if exito and isinstance(res, dict) and res.get("success"):
            keys_generadas.append(key_aleatoria)

    if keys_generadas:
        keys_texto = "\n".join([f"• `{k}`" for k in keys_generadas])
        mensaje = f"📦 **¡Lote Generado!**\n🏷️ `{name}` | ⏳ {days} días\n\n{keys_texto}"
    else:
        mensaje = f"❌ **Error al generar el lote.**"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

@restricted
async def comprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Escribe la key a comprobar.", parse_mode="Markdown")
        return
    
    key = args[0]
    exito, res = llamar_api("check", {"key": key})
    
    if exito and isinstance(res, dict):
        estado = "Activa/Válida" if res.get("success") else "Inválida/Expirada"
        mensaje = f"🔍 **Key:** `{key}`\n📌 **Estado:** {estado}"
    else:
        mensaje = f"❌ **Error:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

@restricted
async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Escribe la key que quieres eliminar.", parse_mode="Markdown")
        return
    
    key = args[0]
    exito, res = llamar_api("delete", {"key": key})
    
    if exito and isinstance(res, dict) and res.get("success"):
        mensaje = f"🗑️ **Key eliminada:**\n`{key}`"
    else:
        mensaje = f"❌ **Error:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Menús generales
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ayuda", menu))
    app.add_handler(CommandHandler("help", menu))
    
    # Menú exclusivo de administrador
    app.add_handler(CommandHandler("menuadmin", menu_admin))
    
    # Comandos exclusivos del Administrador
    app.add_handler(CommandHandler("agregar", agregar_usuario))
    app.add_handler(CommandHandler("borrar_todos", borrar_todos_usuarios))
    
    # Comandos generales para ti y tus usuarios con membresía vigente
    app.add_handler(CommandHandler("generar", generar))
    app.add_handler(CommandHandler("lote", lote))
    app.add_handler(CommandHandler("comprobar", comprobar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    
    print("🤖 ¡Bot actualizado con menú de administración separado!")
    app.run_polling()
