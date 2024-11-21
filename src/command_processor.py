# command_processor.py
import time
import logging
from command_handler import CommandHandler

class CommandProcessor:
    @staticmethod
    def process_command(recognized_text, recognizer):
        if "ayuda" in recognized_text:
            CommandHandler.display_help()
            return
        keyword_found = next((k for k in recognizer.keyword_list if k in recognized_text), None)
        if keyword_found:
            command = recognized_text.split(keyword_found, 1)[-1].strip()
            matched_command = CommandHandler.get_best_match(command)
            current_time = time.time()
            if matched_command and (matched_command != recognizer.last_command_time or current_time - recognizer.last_command_time > 5):
                recognizer.last_command_time = current_time
                CommandHandler.execute_command(matched_command)
                CommandHandler.schedule_training(matched_command, time.localtime().tm_hour)
            else:
                logging.info(f"Comando no reconocido o repetido: {command}")
                # Fallback mechanism
                CommandHandler.fallback_command(command)
