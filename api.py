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
        # 1. Send the link and save OUR message ID to track the specific reply
        sent_msg = await client.send_message(BOT_USERNAME, link)
        
        # 2. Poll the chat, waiting for the bot to reply and finish editing
        # Increased to 60 seconds because your example showed a 28.6s bypass time
        for _ in range(60):
            await asyncio.sleep(1)
            
            # Check the last 30 messages in the chat
            async for msg in client.iter_messages(BOT_USERNAME, limit=30):
                
                # Check if this message is a reply to OUR specific link
                if msg.reply_to_msg_id == sent_msg.id:
                    text = msg.text or ""
                    
                    # 3. Check if the bot has finished editing (looking for the footer)
                    # We also check for common error words just in case the bot fails
                    if "CC : @DDxBypass_Bot" in text or "error" in text.lower() or "failed" in text.lower():
                        
                        # 4. Extract ONLY the bypassed URLs using Regex
                        bypassed_links = re.findall(r'▸ Bypassed ➙\s*(https?://[^\s]+)', text)
                        
                        if bypassed_links:
                            return {
                                "status": "success",
                                # Often the last link in the chain is the one you actually want
                                "final_link": bypassed_links[-1], 
                                "all_links": bypassed_links # Includes intermediate links if there are multiple steps
                            }
                        else:
                            return {
                                "status": "failed",
                                "message": "Bot finished but no bypassed link was found.",
                                "raw_response": text
                            }
        
        return {"status": "error", "message": "Timeout: Bot took longer than 60 seconds to finish."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
