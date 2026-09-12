from chatbot import chatbot

bot = chatbot()

while True:
    message = input("You: ")

    if message.lower() == "exit"
        break

    print("Bot:", bot.reply(message))