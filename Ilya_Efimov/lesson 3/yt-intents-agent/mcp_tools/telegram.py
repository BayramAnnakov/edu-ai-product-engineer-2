import logging
import subprocess
import json
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramMCPClient:
    def __init__(self):
        self.server_url = "https://server.smithery.ai/@NexusX-MCP/telegram-mcp-server"
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    async def detect_send_message_tool(self):
        try:
            cmd = ["mcp", "list-tools", self.server_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tools = data.get("tools", [])
                
                for tool in tools:
                    tool_name = tool.get("name", "").lower()
                    if "send" in tool_name and "message" in tool_name:
                        return tool["name"]
            
            return "send_message"
            
        except Exception as e:
            logger.warning(f"Could not detect send message tool, using default: {e}")
            return "send_message"
    
    def send_document(self, file_path, filename, caption=""):
        """Отправляет документ в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': (filename, file, 'text/markdown')}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"Document sent to Telegram successfully: {filename}")
                    return True
                else:
                    logger.error(f"Telegram API error sending document: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending document to Telegram: {e}")
            return False

    async def send_report(self, report_content, channel_id=None):
        try:
            # For demo purposes with placeholder tokens, simulate successful send
            if self.bot_token == "demo_bot_token" or self.chat_id == "demo_chat_id":
                logger.info("Demo mode: Report would be sent to Telegram")
                print("\n" + "="*60)
                print("📱 TELEGRAM REPORT (Demo Mode)")
                print("="*60)
                print(report_content)
                print("="*60)
                return True
            
            # Check if message is too long (Telegram limit is ~4096 chars)
            if len(report_content) > 4000:
                logger.info("Report too long, sending as file...")
                return self._send_report_as_file(report_content, channel_id)
            
            # Use direct Telegram API instead of MCP
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": report_content,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info("Report sent to Telegram successfully via direct API")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                # If message too long error, try sending as file
                if "message is too long" in response.text.lower():
                    logger.info("Message too long, trying to send as file...")
                    return self._send_report_as_file(report_content, channel_id)
                return False
            
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
    
    def _send_report_as_file(self, report_content, channel_id=None):
        """Отправляет отчет как файл"""
        try:
            import os
            import tempfile
            from datetime import datetime
            
            # Создаем временный файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"youtube_analysis_{channel_id or 'unknown'}_{timestamp}.md"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(report_content)
                tmp_file_path = tmp_file.name
            
            # Отправляем файл
            success = self.send_document(
                tmp_file_path, 
                filename, 
                caption=f"📊 YouTube Analysis Report\n🆔 Channel: `{channel_id or 'Unknown'}`"
            )
            
            # Удаляем временный файл
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending report as file: {e}")
            return False