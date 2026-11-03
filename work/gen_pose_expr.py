import json, urllib.request, time, sys

# gen_poses.py / gen_poses_fix.py を踏襲。ポーズ拡充第一弾の表情差分生成。
# 土台・シード・ポーズ指定は採用候補と同一にし、表情指定だけを差し替える。
#   46 = pose6(seed 20261101) 笑顔
#   47 = pose7 fixA3(seed 20262102) 目閉じ
#   48 = pose8 hug(seed 98101) 笑顔
#   49 = pose9(seed 20261101) 通常（穏やかな顔。基番9の偉そうと対）
#   9H = pose9(seed 20261101) 偉そう強化（基番9の土台候補。seedCの表情へ接近）
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
SMILE_PROSE = (
    "She has a gentle warm smile, her golden eyes open and looking softly at the viewer, "
    "a kind and happy expression. "
)
CALM = "She has a calm gentle expression, her golden eyes looking softly at the viewer. "
EXPR_HAUGHTY = (
    "She looks down at the viewer with half-lidded eyes and a composed, haughty, mildly "
    "condescending expression, as if thoroughly unimpressed. "
)
FIX_HAND_NEG = (
    ", oversized hands, huge hands, big hands, disproportionate hands, long fingers, "
    "floating symbols, emphasis lines, motion lines"
)
SLIT_NEG = (
    ", slit, leg slit, side slit, thigh slit, high slit, dress slit, bare legs, exposed thigh, "
    "shiny fabric, latex, dress train, puddle train"
)
SKIRT_PROSE = (
    "Her long skirt is a single unbroken sweep of matte black fabric with gold trim, falling "
    "straight to her ankles and completely covering both of her legs; there is no slit or "
    "opening anywhere in the skirt. "
)

RUNS = [
    (
        "pose46", 20261101,
        BASE_TAGS
        + "standing, own hands together, hands clasped in front, "
        + EYES_OPEN + "gentle smile, warm smile, happy, "
        + SKIN_DRESS
        + FRAME
        + "standing straight and facing the viewer, her arms lowered in front of her body with "
          "both hands gently clasped together in front of her waist, a calm docile standing "
          "posture, not holding anything. "
        + DRESS_TAIL + SMILE_PROSE + BG_PROSE,
        NEG_BASE + ", frown, angry, closed eyes, sad",
    ),
    (
        "pose47", 20262102,
        BASE_TAGS
        + "three-quarter view, open palms, hands raised, small hands, head bowed, closed eyes, "
        + SKIN_DRESS
        + FRAME
        + "shown in a three-quarter view with her body turned slightly to the side, both open "
          "palms raised in front of her chest in a small flustered gesture, her head slightly "
          "bowed, not holding anything. Her hands are small and delicate, drawn at a natural "
          "size in correct proportion to her petite body, kept close to her chest rather than "
          "thrust toward the viewer. "
        + DRESS_TAIL
        + "She has a soft meek expression with her eyes gently closed, her eyebrows lightly "
          "drawn together in quiet concern, small closed lips. "
        + BG_PROSE,
        NEG_BASE + FIX_HAND_NEG + ", open eyes, looking at viewer",
    ),
    (
        "pose48", 98101,
        BASE_TAGS
        + "holding book, book, old book, "
        + EYES_OPEN + "gentle smile, warm smile, happy, "
        + SKIN_DRESS
        + FRAME
        + "standing straight and facing the viewer, hugging a thick old leather-bound book "
          "against her chest with both arms. "
        + DRESS_TAIL + SMILE_PROSE + BG_PROSE,
        NEG_BASE.replace("holding book, holding object, ", "") + ", frown, angry, closed eyes, sad",
    ),
    (
        "pose49", 20261101,
        BASE_TAGS
        + "arms crossed, crossed arms, "
        + EYES_OPEN + SKIN_DRESS
        + FRAME
        + "standing straight and facing the viewer, her arms firmly crossed over her chest, "
          "a relaxed confident posture, not holding anything. "
        + DRESS_TAIL + CALM + BG_PROSE,
        NEG_BASE + ", half-closed eyes, narrowed eyes, frown, angry, looking down",
    ),
    (
        "pose9h", 20261101,
        BASE_TAGS
        + "arms crossed, crossed arms, looking down, confident, half-closed eyes, "
          "long dress, full-length dress, "
        + EYES_OPEN + SKIN_DRESS
        + FRAME
        + "standing straight and facing the viewer, her arms firmly crossed over her chest, "
          "her chin slightly raised in a confident posture, not holding anything. "
        + DRESS_TAIL + SKIRT_PROSE + EXPR_HAUGHTY + BG_PROSE,
        NEG_BASE + SLIT_NEG,
    ),
]

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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"astaroth_{label}_seed{seed}"}}
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
            outs=h[pid].get("outputs",{})
            print("RUN", label, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("RUN", label, "TIMEOUT", flush=True)
    return 3

rc = 0
for (label, seed, pos, neg) in RUNS:
    r = run(label, seed, pos, neg)
    if r != 0:
        rc = r
        print("failed", label, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
