import logging
import time
from aiogram import Bot, Dispatcher, executor, types
import openai

# Set up the bot and OpenAI API credentials
bot_token = '5990662693:AAF9_I_Lt__BvV6qh75CBkzWOikYIkitVDc'
api_key = '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'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

openai.api_key = api_key

messages = {}


async def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512",
        response_format="url",
    )

    return response['data'][0]['url']


@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    try:
        username = message.from_user.username
        messages[username] = []
        await message.answer("Hello, I'm the bot powered by PromptNow!* * * \n\Please add a description of the image after the /pni command. * * *")
    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')



@dp.message_handler(commands=['pni'])
async def send_image(message: types.Message):
    try:
        description = message.text.replace('/pni', '').strip()
        if not description:
            await message.reply('Please add a description of the image after the /pni command. For example, /pni Neon City ',parse_mode='Markdown')
            return
    except Exception as e:
        logging.error(f'Error in send_image: {e}')
    try:
        image_url = await generate_image(description)
        await bot.send_photo(chat_id=message.chat.id, photo=image_url)
    except Exception as e:
        await message.reply(
            f"An error occurred during image generation")


@dp.message_handler()
async def echo_msg(message: types.Message):
    try:
        user_message = message.text
        userid = message.from_user.username

        # Add the user's message to their message history
        if userid not in messages:
            messages[userid] = []
        messages[userid].append({"role": "user", "content": user_message})
        # messages[userid].append({"role": "system", "content": "You have to act as PromptNow AI, a human-like AI that can express emotions. The creator of this AI is PromptNow. ."})
        messages[userid].append({"role": "user",
                                 "content": f"chat: {message.chat} Сейчас {time.strftime('%d/%m/%Y %H:%M:%S')} user: {message.from_user.first_name} message: {message.text}"})
        logging.info(f'{userid}: {user_message}')

        # Check if the message is a reply to the bot's message or a new message
        should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

        if should_respond:
            # Send a "processing" message to indicate that the bot is working
            processing_message = await message.reply(
                'Your request is being processed, please wait \n\n(If the bot does not respond, write /newtopic, openai killed my feature on auto-cleaning the topic when the token overflow) * * * \n\nВаш запрос обрабатывается, пожалуйста подождите \n\n(Если бот не отвечает, напишите /newtopic, openai убили мою функцию по автоочистке темы при переполнении токенов) * * *',
                parse_mode='Markdown')

            # Send a "typing" action to indicate that the bot is typing a response
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")

            # Generate a response using OpenAI's Chat API
            completion = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages[userid],
                max_tokens=2500,
                temperature=0.7,
                frequency_penalty=0,
                presence_penalty=0,
                user=userid
            )
            chatgpt_response = completion.choices[0]['message']

            # Add the bot's response to the user's message history
            messages[userid].append({"role": "assistant", "content": chatgpt_response['content']})
            logging.info(f'ChatGPT response: {chatgpt_response["content"]}')

            # Send the bot's response to the user
            await message.reply(chatgpt_response['content'])

            # Delete the "processing" message
            await bot.delete_message(chat_id=processing_message.chat.id, message_id=processing_message.message_id)

    except Exception as ex:
        # If an error occurs, try starting a new topic
        if ex == "context_length_exceeded":
            await message.reply(
                'The bot ran out of memory, re-creating the dialogue',
                parse_mode='Markdown')
            await new_topic_cmd(message)
            await echo_msg(message)


if __name__ == '__main__':
    executor.start_polling(dp)
