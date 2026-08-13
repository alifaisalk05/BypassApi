import re
from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
import uvicorn

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")
BOT_USERNAME = "@DDxBypass_Bot"

app = FastAPI()

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
        # 1. Send the link and save OUR message ID
        sent_msg = await client.send_message(BOT_USERNAME, link)
        
        # 2. Poll for the reply
        for _ in range(60):
            await asyncio.sleep(1)
            
            # Check recent messages to find the bot's reply to our specific message
            async for msg in client.iter_messages(BOT_USERNAME, limit=10):
                if msg.reply_to_msg_id == sent_msg.id:
                    text = msg.text or ""
                    
                    # 3. Look for "Bypassed" followed by a URL on the same line.
                    # (?i) makes it case-insensitive so it catches "Bypassed", "bypassed", etc.
                    # [^\n]* allows any characters (like ➙, -, or spaces) before the http link
                    bypassed_links = re.findall(r'(?i)bypassed[^\n]*(https?://[^\s]+)', text)
                    
                    if bypassed_links:
                        # As soon as we see a bypassed link, we return it instantly.
                        return {
                            "status": "success",
                            "final_link": bypassed_links[-1], # Grabs the last link in the chain
                            "all_links": bypassed_links       # In case it's a multi-step bypass
                        }
                        
                    # Catch obvious error messages from the bot so it doesn't hang for 60 seconds
                    if "error" in text.lower() or "invalid link" in text.lower():
                        return {"status": "error", "message": text}

        return {"status": "error", "message": "Timeout: No bypassed link found within 60 seconds."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
