import json, urllib.request, time, sys

# フルフル通常絵（surface10）候補生成。gen_shell.py（アスタロト）を踏襲し、
# キャラ仕様だけ FURFUR_DESIGN.md 2章に差し替えたもの。
SEEDS = [20261103, 1031, 777003]

positive = (
"masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
"white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, round pupils, "
"pinkish skin, blush, cheerful smile, gentle smile, happy, "
"pink frilled dress, frilled knee-length dress with flared skirt, white frills, pink heeled shoes, "
"white feather wings, two small white feather wings on her back, "
"A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
"her whole body from the top of her head to the tips of her shoes fully visible inside the frame "
"with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
"hands empty. She wears a cute pink frilled dress with a flared skirt ending above her knees. "
"Two small white feather wings spread slightly behind her back, modest in size, fully visible "
"inside the frame and not too large. She has a cheerful gentle smile, her sparkling blue eyes "
"open and looking at the viewer, bright and energetic. "
"Behind her is a completely plain solid bright green background, a single flat uniform green "
"color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
"no gradient. Clean silhouette, hair, wings and dress clearly separated from the green background."
)
negative = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
"deer, antlers, horns, tail, animal ears, huge wings, giant wings, closed eyes, frown, angry"
)

def run(seed):
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":positive}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":negative}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"furfur_base_seed{seed}"}}
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
        print("seed failed", s, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
