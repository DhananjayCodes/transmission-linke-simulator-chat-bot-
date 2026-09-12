from chatbot import Chatbot

bot = Chatbot()

while True:
    message = input("You: ")

    if message.lower() == "exit":
        break

    print("Bot:", bot.reply(message))