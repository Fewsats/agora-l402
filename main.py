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
import asyncio
from anthropic.types import ToolUseBlock


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

os.environ['ANTHROPIC_LOG'] = 'debug'

messages = []
history = None

# Chat message component (renders a chat bubble)
def ChatMessage(msg):
    bubble_class = "chat-bubble-primary" if msg['role']=='user' else 'chat-bubble-secondary'
    chat_class = "chat-end" if msg['role']=='user' else 'chat-start'
    return Div(Div(msg['content'], cls=f"chat-bubble {bubble_class}"),
               cls=f"chat {chat_class}")


def ChatInput(text=""):
    return Div(
        Input(placeholder='Message assistant', 
              value=text,
              cls='resize-none border-none outline-none bg-transparent w-full shadow-none ring-0 focus:ring-0 focus:outline-none hover:shadow-none text-lg',
              id='msg-input',
              name='msg'),
        id='chat-input-container',
        hx_swap_oob='true'
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
    history = None
    return chat_layout()


sample_item = '{"name": "Headphones", "storeName": "The Baby Cubby", "brand": "Tonies", "_id": "6674b4aab49534201189688d", "slug": "tonies-headphones-08c2c9a1-b3af-4883-aebf-2a283a1fc0fd-1718924458056", "price": 29.99, "isVerified": false, "isBoosted": false, "source": "shopify", "images": ["https://cdn.shopify.com/s/files/1/0467/0649/1556/products/Heaphones-PDP-Assets-Gray-1.jpg?v=1637054130", "https://cdn.shopify.com/s/files/1/0467/0649/1556/products/Heaphones-PDP-Assets-Gray-2.jpg?v=1637054132", "https://cdn.shopify.com/s/files/1/0467/0649/1556/products/Heaphones-PDP-Assets-Gray-3.jpg?v=1637054134", "https://cdn.shopify.com/s/files/1/0467/0649/1556/products/blue_8b41cdb7-1f12-4b3d-b43c-8aac607377f3.jpg?v=1637336366", "https://cdn.shopify.com/s/files/1/0467/0649/1556/products/Heaphones-PDP-Assets-Pink-1.jpg?v=1637336366", "https://cdn.shopify.com/s/files/1/0467/0649/1556/products/Reddd.jpg?v=1637336366"], "url": "https://babycubby.com/products/tonies-headphones", "agoraScore": 92, "priceHistory": [{"price": 29.99, "date": "2024-06-20T23:24:59.057Z", "_id": "6713d5706ca0a1804a53068e"}], "discountVal": 0}'

def get_tool_result(tc: ToolUseBlock, history: list):
    tr =  [tr for tr in history[-1].content if tr.type == 'tool_result' and tr.tool_use_id == tc.id]
    assert len(tr) == 1
    return first(tr).content

@app.ws('/wscon')
async def submit(msg: str, send=None):
    global history
    swap = 'beforeend'
    target = 'chatlist'

    messages.append(mk_msg(msg))
    await send(Div(ChatMessage(messages[-1]), hx_swap_oob=swap, id=target))
    await send(ChatInput())
    
    await asyncio.sleep(1) # to allow chat to be cleared before the next blocking call

    # Instead of async display_product, we use synchronous ProductCard.
    # Define a manual tool loop: call the chat once with the incoming msg.
    sp = 'You assist users searching for products in a store. When displaying a product, use the ProductCard tool.'
    chat = Chat(models[1], sp=sp, tools=[search_trial, ProductCard])
    if history: chat.h = history

    r = chat(msg)
    iteration = 0
    # Loop until the assistant is finished or max iterations reached.
    while r.stop_reason == 'tool_use' and iteration < 10:
        # Check for a tool call that should update the UI (e.g., ProductCard).
        tc = first([o for o in r.content if isinstance(o, ToolUseBlock)])
        
        if tc.name == 'ProductCard':
            tr = get_tool_result(tc, chat.h)
            await send(Div(NotStr(tr), hx_swap_oob=swap, id=target))

        # Otherwise, continue the tool loop normally.
        r = chat()
        iteration += 1

    history = chat.h
    print('History: ', history)
    messages.append({"role": "assistant", "content": contents(r)})
    await send(Div(ChatMessage(messages[-1]), hx_swap_oob=swap, id=target))


if __name__ == '__main__': uvicorn.run("main:app", host='0.0.0.0', port=5039, reload=True)