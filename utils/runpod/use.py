#è importante usare max_new_token > 200 per non tagliare la fine del json
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import torch, json, re

base_id = "mistralai/Mistral-7B-Instruct-v0.3"
adapters = "out-mistral-json/final"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)

tok = AutoTokenizer.from_pretrained(base_id)
tok.pad_token = tok.eos_token
tok.padding_side = "left"

base = AutoModelForCausalLM.from_pretrained(base_id, quantization_config=bnb, device_map="auto")
model = PeftModel.from_pretrained(base, adapters).eval()

CTX = getattr(model.config, "max_position_embeddings", 8192)  # fallback 8k

def infer(article: str, max_new_tokens=500):
    msgs = [
        {"role":"system","content":"Restituisci SOLO JSON valido."},
        {"role":"user","content": f"<ARTICLE>{article}</ARTICLE>"}
    ]
    # ottieni direttamente gli ids
    inp = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)

    # riserva spazio per l’output
    max_in = CTX - max_new_tokens
    if inp.shape[1] > max_in:   # taglia dalla testa, preserva la fine (dove c'è l'istruzione)
        inp = inp[:, -max_in:]

    with torch.inference_mode():
        out = model.generate(
            input_ids=inp,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=tok.eos_token_id,
            pad_token_id=tok.eos_token_id,
        )

    gen_ids = out[0, inp.shape[1]:]              # SOLO i nuovi token
    txt = tok.decode(gen_ids, skip_special_tokens=True).strip()

    # estrai JSON robustamente
    m = re.search(r"\{.*\}", txt, flags=re.S)
    obj = json.loads(m.group(0)) if m else None
    return txt, obj
