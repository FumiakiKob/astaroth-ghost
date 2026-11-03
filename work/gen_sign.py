import json, urllib.request, time, sys

# 不在看板（surface26〜30）の土台生成。文字なしの木製立て看板だけを描き、
# 文字は finalize_sign.py で PIL 合成する（AI に文字を描かせない）。
# ワークフローは gen_sitting.py と同一ブループリント（CottonAnima base1、
# 832x1216、30step/CFG4/er_sde、緑背景）。このスクリプトは WSL 内で実行する。

POSITIVE = (
    "masterpiece, best quality, score_7, no humans, still life, object focus, "
    "a blank wooden standing signboard, one wide plain wooden plank board mounted "
    "on a single sturdy wooden pole stand, rustic natural light-brown wood planks, "
    "the board is completely blank and empty with no text, no letters and no markings, "
    "front view, centered, the whole signboard from the top of the board to the bottom "
    "of the stand fully visible inside the frame with generous margin around it. "
    "Behind it is a completely plain solid bright green background, a single flat "
    "uniform green color filling the entire background, chroma key green screen, "
    "no scenery, no floor, no shadows, no gradient. Clean silhouette, the wooden "
    "signboard clearly separated from the green background."
)
NEGATIVE = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "text, letters, words, alphabet, numbers, writing, calligraphy, logo, watermark, "
    "1girl, girl, woman, person, human, character, face, hands, animal, "
    "scenery, indoors, outdoors, gradient background, multiple signboards, "
    "cropped, out of frame, cut off, photo, photorealistic, 3d render"
)
SEEDS = [26101, 26102, 26103]

def run(seed):
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":POSITIVE}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":NEGATIVE}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"sign_base_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("SEED", seed, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("SEED", seed, "TIMEOUT", flush=True)
    return 3

rc = 0
for s in SEEDS:
    r = run(s)
    if r != 0:
        rc = r
        print("failed", s, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
