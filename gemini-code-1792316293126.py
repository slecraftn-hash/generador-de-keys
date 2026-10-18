import json
import urllib.parse
import urllib.request
import urllib.error
import secrets
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Tus datos de la API
API_BASE = "http://155.117.40.185:10068"
ADMIN_API_KEY = "Wen0PWx!loa"

# Token de tu bot
TOKEN = "8998224860:AAHCxlM3GKXvrG7rgw_ZIpyfTR-44Of-9gk"

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

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_menu = (
        "🤖 **MENÚ DE GESTIÓN DE KEYS** 🤖\n\n"
        "Aquí tienes la lista de comandos disponibles:\n\n"
        "• `/generar` [días]\n"
        "  _Genera una key individual con prefijo csw_._\n"
        "  Ejemplo: /generar 30\n\n"
        "• `/lote` [nombre] [cantidad] [días]\n"
        "  _Genera múltiples keys con prefijo csw_._\n"
        "  Ejemplo: /lote casawa 5 30\n\n"
        "• `/comprobar` [key]\n"
        "  _Revisa si una key está activa o expirada._\n"
        "  Ejemplo: /comprobar csw_12345\n\n"
        "• `/eliminar` [key]\n"
        "  _Borra una key del sistema._\n"
        "  Ejemplo: /eliminar csw_12345\n\n"
        "• `/menu` o `/ayuda`\n"
        "  _Muestra este menú de ayuda._"
    )
    await update.message.reply_text(texto_menu, parse_mode="Markdown")

async def generar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    days = args[0] if args else "10"
    
    key_aleatoria = f"csw_{secrets.token_hex(4).upper()}"
    
    exito, res = llamar_api("generate", {"key": key_aleatoria, "days": days})
    
    if exito and isinstance(res, dict) and res.get("success"):
        mensaje = (
            f"✅ **¡Key Generada con Éxito!**\n\n"
            f"🔑 `{key_aleatoria}`\n"
            f"⏳ **Duración:** {days} días"
        )
    else:
        mensaje = f"❌ **Error al generar key:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def lote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ **Formato incorrecto.**\nUsa: `/lote` [nombre] [cantidad] [días]\nEjemplo: /lote casawa 5 30",
            parse_mode="Markdown"
        )
        return
    
    name = args[0]
    try:
        count = int(args[1])
        days = args[2]
    except ValueError:
        await update.message.reply_text("⚠️ La cantidad debe ser un número entero.", parse_mode="Markdown")
        return

    if count > 30:
        await update.message.reply_text("⚠️ Por favor solicita un máximo de 30 keys por lote para evitar demoras.", parse_mode="Markdown")
        return

    keys_generadas = []
    
    for _ in range(count):
        key_aleatoria = f"csw_{secrets.token_hex(4).upper()}"
        exito, res = llamar_api("generate", {"key": key_aleatoria, "days": days})
        if exito and isinstance(res, dict) and res.get("success"):
            keys_generadas.append(key_aleatoria)

    if keys_generadas:
        keys_texto = "\n".join([f"• `{k}`" for k in keys_generadas])
        mensaje = (
            f"📦 **¡Lote Generado con Éxito!**\n\n"
            f"🏷️ **Nombre:** `{name}`\n"
            f"⏳ **Duración:** {days} días\n"
            f"🔢 **Total:** {len(keys_generadas)} keys\n\n"
            f"{keys_texto}"
        )
    else:
        mensaje = f"❌ **Error al generar el lote de keys.**"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def comprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Escribe la key. Ejemplo: /comprobar csw_12345", parse_mode="Markdown")
        return
    
    key = args[0]
    exito, res = llamar_api("check", {"key": key})
    
    if exito and isinstance(res, dict):
        estado = "Activa/Válida" if res.get("success") else "Inválida/Expirada"
        mensaje = (
            f"🔍 **Consulta de Key**\n\n"
            f"🔑 **Key:** `{key}`\n"
            f"📌 **Estado:** {estado}"
        )
    else:
        mensaje = f"❌ **Error al consultar:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Escribe la key que quieres eliminar. Ejemplo: /eliminar csw_12345", parse_mode="Markdown")
        return
    
    key = args[0]
    exito, res = llamar_api("delete", {"key": key})
    
    if exito and isinstance(res, dict) and res.get("success"):
        mensaje = f"🗑️ **Key eliminada correctamente:**\n`{key}`"
    else:
        mensaje = f"❌ **Error al eliminar:**\n`{res}`"
        
    await update.message.reply_text(mensaje, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ayuda", menu))
    app.add_handler(CommandHandler("help", menu))
    
    app.add_handler(CommandHandler("generar", generar))
    app.add_handler(CommandHandler("lote", lote))
    app.add_handler(CommandHandler("comprobar", comprobar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    
    print("🤖 ¡Bot de Telegram iniciado y operativo en t.me/casawa_bot!")
    app.run_polling()