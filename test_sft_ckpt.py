import logging
from dataset.validation import val_set_sft
import torch
from deepspeed.utils.zero_to_fp32 import get_fp32_state_dict_from_zero_checkpoint
from models.tokenization_guyu import GuyuTokenizer
from models.configuration_guyu import GuyuConfig
from models.modeling_guyu import GuyuForCausalLM

tokenizer = GuyuTokenizer("configs/tokenizer_models/32k_vocab_guyu_pajama_pj.model", legacy=False)
# tokenizer = LlamaTokenizer.from_pretrained("data/saved_ckpt/7B_FP16", use_fast=False)

def load_ckpt():
    model_config = GuyuConfig.from_pretrained("configs/model_configs/1B.json")
    #model = GuyuForCausalLM.from_pretrained('./ckpt/1B/',config=model_config)
    # unwrapped_model = accelerator.unwrap_model(model)
    model = GuyuForCausalLM(config=model_config)
    state_dict = get_fp32_state_dict_from_zero_checkpoint("ckpt/1B_instruction/")
    model = model.cpu()
    model.load_state_dict(state_dict)
    # model.load_state_dict(torch.load("data/saved_ckpt/7B/pytorch_model.bin"))
    logging.warning("loading complete")
    model.eval()
    model = model.half().cuda()
    logging.warning("ready")
    return model

def load_pretrained():
    model_config = GuyuConfig.from_pretrained("configs/model_configs/1B.json")
    model = GuyuForCausalLM.from_pretrained('./ckpt/1B_instruction',config=model_config)
    logging.warning("loading complete")
    model.eval()
    model = model.half().cuda()
    logging.warning("ready")
    return model

#model = load_ckpt()
model = load_pretrained()

for data in val_set_sft:
    raw_inputs = data
    inputs = tokenizer(
        raw_inputs,
        return_tensors="pt",
        add_special_tokens=False,
        return_attention_mask=False,
    )
    input_length = inputs["input_ids"].shape[1]
    for k, v in inputs.items():
        inputs[k] = v.cuda()
    pred = model.generate(
        **inputs, max_new_tokens=256, do_sample=True, repetition_penalty=2.0
    )
    pred = pred[0, input_length:]
    pred = tokenizer.decode(pred.cpu(), skip_special_tokens=True)
    print(raw_inputs, '\n', pred, '\n')