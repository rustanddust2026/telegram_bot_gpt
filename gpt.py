from openai import OpenAI
import httpx as httpx


class ChatGptService:
    client: OpenAI = None
    message_list: list = None

    def __init__(self, token):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = OpenAI(
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"),
            api_key=token)
        self.message_list = []

    async def send_message_list(self) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # gpt-4o,  gpt-4-turbo,    gpt-3.5-turbo,  GPT-4o mini
            messages=self.message_list,
            max_tokens=3000,
            temperature=0.9)
        message = completion.choices[0].message
        self.message_list.append(message)
        return message.content

    def set_prompt(self, prompt_text: str) -> None:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    def speech_to_text(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcription.text

    def text_to_speech(self, text: str, output_path: str) -> None:
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="opus",
        )
        response.stream_to_file(output_path)
