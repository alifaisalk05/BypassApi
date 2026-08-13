from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
import uvicorn

# Fetch credentials from Render environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")
BOT_USERNAME = "@DDxBypass_Bot"

app = FastAPI()

# Initialize the Telethon client using a String Session (stateless, perfect for Render)
# Fallback to None if environment variables aren't set during build
if API_ID and API_HASH and SESSION:
    client = TelegramClient(StringSession(SESSION), int(API_ID), API_HASH)
else:
    client = None

@app.on_event("startup")
async def startup_event():
    if client:
        await client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    if client:
        await client.disconnect()

@app.get("/")
async def process_link(link: str):
    if not client:
        raise HTTPException(status_code=500, detail="Telegram credentials missing in environment variables.")
    
    try:
        # Send the link to the bot
        await client.send_message(BOT_USERNAME, link)
        
        # Poll for the bot's reply (wait up to 15 seconds)
        for _ in range(15):
            await asyncio.sleep(1)
            messages = await client.get_messages(BOT_USERNAME, limit=1)
            
            # Check if the last message is from the bot (not from you)
            if messages and not messages[0].out:
                return {
                    "status": "success", 
                    "original": link, 
                    "result": messages[0].text
                }
                
        return {"status": "error", "message": "Bot did not respond within 15 seconds"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Render assigns a dynamic port via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
