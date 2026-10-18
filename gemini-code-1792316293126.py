import json
import urllib.parse
import urllib.request
import urllib.error
import secrets
from functools import wraps
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Tus datos de la API
API_BASE = "http://155.117.40.185:10068"
ADMIN_API_KEY = "Wen0PWx!loa"

# Token de tu bot
TOKEN = "8998224860:AAHCxlM3GKXvrG7rgw_ZIpyfTR-44Of-9gk"

# Tu ID de Telegram verificado
ADMIN_IDS = [8046948909]

# Lista donde se guardarán los usernames autorizados dinámicamente
USUARIOS_AUTORIZADOS = [] 

def restricted(func):
    """Decorador para permitir el acceso solo al admin principal o usuarios autorizados"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Permitir si es el admin principal o si su username está en la lista autorizada
        if user_id not in ADMIN_IDS and (not username or username.lower() not in [u.lower() for u in USUARIOS_AUTORIZADOS]):
            await update.message.reply_text("⛔ **Acceso denegado.** No tienes autorización para usar este bot.")
            return
        return await func(update, context)
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
        "• `/agregar` [username]\n"
        "  _Da acceso a un nuevo usuario por su nombre (Ej: /agregar juanito)_\n\n"
        "• `/menu`\n"
        "  _Muestra este menú_"
    )
    await update.message.reply_text(texto_menu, parse_mode="Markdown")

@restricted
async def agregar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando exclusivo para agregar usuarios por su username"""
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Escribe el username. Ejemplo: `/agregar nombreusuario`", parse_mode="Markdown")
        return
    
    nuevo_user = args[0].replace("@", "").strip()
    if nuevo_user.lower() not in [u.lower() for u in USUARIOS_AUTORIZADOS]:
        USUARIOS_AUTORIZADOS.append(nuevo_user)
        await update.message.reply_text(f"✅ ¡Usuario **@{nuevo_user}** agregado exitosamente a los autorizados!", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"ℹ️ El usuario **@{nuevo_user}** ya estaba en la lista.", parse_mode="Markdown")

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
    
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ayuda", menu))
    app.add_handler(CommandHandler("help", menu))
    
    app.add_handler(CommandHandler("agregar", agregar_usuario))
    app.add_handler(CommandHandler("generar", generar))
    app.add_handler(CommandHandler("lote", lote))
    app.add_handler(CommandHandler("comprobar", comprobar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    
    print("🤖 ¡Bot de Telegram iniciado y operativo en t.me/casawa_bot!")
    app.run_polling()

