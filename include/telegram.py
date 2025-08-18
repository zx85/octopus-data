from include.logger import log

# pip library python-telegram-bot (I'm using 12.8)
import telegram

class TelegramBot():
  def __init__(self, bot_token, chat_id):
     self.chat_id=chat_id
     self.bot=telegram.Bot(token=bot_token)

  # Push message doings
  def send_telegram_message(self,date_query, overnight):
      log.debug(f"running sendmessage function - chat_id is {self.chat_id}")
      log.debug("Building telegram message with overnight data")
      total_consumed = 0
      total_cost = 0
      message_str = f"Overnight usage for {date_query}:\n"
      for hh in overnight:
          message_str += (
              hh["hour"]
              + ":"
              + hh["minute"]
              + " - "
              + "{0:.3f}".format(hh["consumed"])
              + "kWh @ £"
              + "{0:.2f}".format(hh["price"] / 100)
              + "\n"
          )
          total_consumed += hh["consumed"]
          total_cost += hh["consumed"] * hh["price"] / 100
      message_str += f"Consumed: {'{0:.3f}'.format(total_consumed)}kWh\nCost: £{'{0:.2f}'.format(total_cost)}"
      log.debug(f"Sending the telegram message: {message_str}")

      self.bot.send_message(chat_id=self.chat_id, text=message_str)
