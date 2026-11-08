import json, urllib.request, time, sys
# pose9face: pose9 composition, calm/gentle expression candidates for face transplant donor.
# Pose prose identical to gen_pose_expr.py pose49; expression strengthened slightly
# (relaxed brows + very slight smile) so the calm reads clearly vs base9's haughty.
BASE_TAGS = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "deep purple and violet hair, long hair, wavy hair, choppy bangs, "
)
EYES_OPEN = "golden amber eyes, round pupils, "
SKIN_DRESS = (
    "(pale skin:0.3), gold pendant, halo, "
    "black and gold off-shoulder dress, elegant long dress with gold trim, "
    "gold chain necklace with demon crest pendant, black heeled shoes, "
)
FRAME = (
    "A petite fallen angel girl in a full body shot, "
    "her whole body from the top of her halo to the tips of her shoes fully visible inside the frame "
    "with margin around her, "
)
DRESS_TAIL = "She wears an elegant black and gold off-shoulder dress. "
BG_PROSE = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair and dress clearly separated from the green background."
)
NEG_BASE = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "furniture, gradient background, multiple girls, holding book, holding object, sitting"
)
CALM_STRONG = (
    "She has a calm, gentle and relaxed expression, her golden eyes fully open and looking "
    "softly at the viewer, her eyebrows relaxed and slightly raised, with a very soft faint "
    "smile on her small lips, a serene and kind mood, completely unlike a haughty glare. "
)
RUNS = []
for seed in [20261101, 20261102, 20261103, 20261104, 20261105, 20261106]:
    RUNS.append((
        f"pose49c{seed}", seed,
        BASE_TAGS
        + "arms crossed, crossed arms, "
        + EYES_OPEN + SKIN_DRESS
        + FRAME
        + "standing straight and facing the viewer, her arms firmly crossed over her chest, "
          "a relaxed confident posture, not holding anything. "
        + DRESS_TAIL + CALM_STRONG + BG_PROSE,
        NEG_BASE + ", half-closed eyes, narrowed eyes, frown, angry, looking down, smug, condescending",
    ))

def run(label, seed, positive, negative):
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":positive}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":negative}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"astaroth_{label}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("RUN", label, "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            print("RUN", label, "STATUS", st.get("status_str"), flush=True)
            return 0 if st.get("completed") else 2
    print("RUN", label, "TIMEOUT", flush=True)
    return 3

rc=0
for (label, seed, pos, neg) in RUNS:
    r=run(label, seed, pos, neg)
    if r!=0: rc=r; print("failed", label, r, flush=True)
print("DONE rc=", rc)
sys.exit(rc)
