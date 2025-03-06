from fasthtml.common import *
from claudette import *
from monsterui.all import *
from typing import List
from dotenv import load_dotenv
import whisper
import uuid
from pathlib import Path
from functools import partial
from agora_l402.core import *


load_dotenv()

# Style to add blinking to an icon
blink = Style("""
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0 !important; }
        100% { opacity: 1; }
    }
    .blink {
        animation: blink 1.5s infinite;
    }
""")

hdrs = Theme.blue.headers(), Script(src="/js/record.js"), blink
app, rt = fast_app(hdrs=hdrs, exts='ws', static_path='public', live=True)

upload_dir = Path("public")
upload_dir.mkdir(exist_ok=True)

model = whisper.load_model("tiny.en")


sp = 'You assist users searching for products in a store and visualizing their shopping cart.'
# chat = Chat(models[1], sp=sp)
chat = Chat(models[1], sp=sp, tools=[search_trial])
os.environ['ANTHROPIC_LOG'] = 'debug'

messages = []

# Chat components
# def UsrMsg(content, content_id):
#     if isinstance(content, list):
#         content = [x['text'] for x in content if x['type'] == 'text'][0]

#     txt_div = Div(content, id=content_id, cls='whitespace-pre-wrap break-words')
#     return Div(txt_div,
#             cls='max-w-[70%] ml-auto rounded-3xl bg-[#f4f4f4] px-5 py-2.5 rounded-tr-lg')

# def AIMsg(txt, content_id):
#     avatar = Div(UkIcon('bot', height=24, width=24),
#                  cls='h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center')
#     txt_div = Div(txt, id=content_id, cls='whitespace-pre-wrap break-words ml-3')
#     return Div(
#         Div(avatar, txt_div, cls='flex items-start'),
#         cls='max-w-[70%] rounded-3xl px-5 py-2.5 rounded-tr-lg'
#     )

# def ChatMessage(msg_idx):
#     msg = messages[msg_idx]
#     content_id = f"chat-content-{msg_idx}"
#     if msg['role'] == 'user':
#         return UsrMsg(msg['content'], content_id)
#     else:
#         return AIMsg(msg['content'], content_id)

# Chat message component (renders a chat bubble)
def ChatMessage(msg):
    bubble_class = "chat-bubble-primary" if msg['role']=='user' else 'chat-bubble-secondary'
    chat_class = "chat-end" if msg['role']=='user' else 'chat-start'
    return Div(Div(msg['content'], cls=f"chat-bubble {bubble_class}"),
               cls=f"chat {chat_class}")


def ChatInput(text=""):
    return (Div(id="image-previews", cls="flex flex-wrap gap-1 mb-2"),  # Container for thumbnails
            Input(placeholder='Message assistant', 
            value=text,
            cls='resize-none border-none outline-none bg-transparent w-full shadow-none ring-0 focus:ring-0 focus:outline-none hover:shadow-none text-lg',
            id='msg-input',
            name='msg',
            hx_swap_oob='true')
    )

def MultimodalInput():
    return Form(
        Div(
            Div(
                ChatInput(),
                DivFullySpaced(
                    DivHStacked(
                        Label(
                            UkIconLink('mic', height=24, width=24, 
                                     cls='hover:opacity-70 transition-opacity duration-200',
                                     id='mic-icon'),
                            UkIconLink('circle-stop', height=24, width=24,
                                     cls='hidden hover:opacity-70 transition-opacity duration-200 blink',
                                     id='stop-icon'),
                            id="mic-btn"
                        )
                    ),
                    Button(UkIcon('arrow-right', height=24, width=24), 
                          cls='bg-black text-white rounded-full hover:opacity-70 h-8 w-8 transform -rotate-90'),
                    cls='px-3'
                )
            ), 
            cls='p-2 bg-[#f4f4f4] rounded-3xl'
        ),
        ws_send=True, 
        hx_ext="ws", 
        ws_connect="/wscon"
    )

def chat_layout():
    return Div(
        DivVStacked(
            H1("Chat UI", cls='m-2'),
            Div(
                *[ChatMessage(msg_idx) for msg_idx, msg in enumerate(messages)],
                id="chatlist",
                cls='space-y-6 overflow-y-auto flex-1 w-full' 
            ),
            Footer(
                MultimodalInput(),
                cls='p-4 bg-white border-t w-full'
            ),
            cls='h-screen flex flex-col max-w-3xl mx-auto w-full'
        ),
        cls='container w-full px-4'
    )



@rt('/transcribe-voice', methods=['POST'])
async def transcribe_voice(request):
    form = await request.form()
    file_obj = form["audio"]
    data = await file_obj.read()
    fname = upload_dir / f"{uuid.uuid4()}.mp3"
    with open(fname, "wb") as f: f.write(data)
    result = model.transcribe(str(fname))
    fname.unlink()
    return result["text"].strip()

@app.route("/")
def get():
    messages = [] # clear session
    return chat_layout()


@app.ws('/wscon')
async def submit(msg: str, send = None):
    swap = 'beforeend'
    target = 'chatlist'


    messages.append(mk_msg(msg))
    # Immediately show user message in chat
    await send(Div(ChatMessage(messages[-1]), hx_swap_oob='beforeend', id="chatlist"))


    # Clear input field via OOB swap
    await send(ChatInput())

    r = chat.toolloop(msg)

    # Get and send the model response
    messages.append({"role":"assistant", "content":contents(r)})
    await send(Div(ChatMessage(messages[-1]), hx_swap_oob=swap, id=target))


# LLM Tools
serve(port=5039)