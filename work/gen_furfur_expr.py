import json, urllib.request, time, sys

# フルフル表情差分生成。gen_expr.py（アスタロト）を踏襲。
# usage: gen_furfur_expr.py <base_seed>
# 基準シード（surface10 採用シード）を第1候補にし、表情ごとに別シード2つを添える。
BASE_SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261103

BASE_TAGS = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "white hair, twintails, hair just past shoulders, curled hair ends, "
    "small pink hair ties, long face-framing sidelocks, choppy bangs, "
)
EYES_OPEN = "starry sparkling cyan-blue eyes, star-shaped highlights in eyes, round pupils, "
SKIN_DRESS = (
    "pinkish skin, blush, "
    "pink sleeveless dress, white frilled shoulder straps, small white bow, "
    "white lace-up criss-cross ribbon on the front of the bodice, gathered waist, "
    "flared skirt with a thin white line near the hem, white frilled petticoat hem under the skirt, "
    "pink mary jane shoes with ankle straps, "
    "white feather wings, two large white feather wings spread horizontally behind her shoulders, "
)
BODY_PROSE = (
    "A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
    "her whole body from the top of her head to the tips of her shoes fully visible inside the frame "
    "with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
    "hands empty. She is always the same girl with the same face, the same starry sparkling "
    "cyan-blue eyes, the same white twintails with curled ends and pink hair ties, and the same "
    "outfit: a pink sleeveless dress with white frilled shoulder straps, a small white bow and a "
    "white lace-up criss-cross ribbon on the front of the bodice, and a white frilled petticoat "
    "hem under the flared skirt. Two large white feather wings spread horizontally behind her "
    "shoulders at shoulder height, fully visible inside the frame. "
)
BG_PROSE = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair, wings and dress clearly separated from the green background."
)
NEG_BASE = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
    "halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
    "deer, antlers, horns, tail, animal ears, huge wings, giant wings"
)

EXPRS = {
    11: {  # 満面の笑顔
        "tags": EYES_OPEN + "big smile, open mouth smile, :d, very happy, joyful, laughing, ",
        "prose": "She has a big joyful open-mouth smile, beaming happily at the viewer, full of energy and delight. ",
        "neg": ", frown, angry, closed eyes, sad, calm expression",
    },
    12: {  # 驚き
        "tags": "starry sparkling cyan-blue eyes, wide eyes, surprised, raised eyebrows, open mouth, :o, ",
        "prose": "She looks genuinely surprised, her eyes wide open, her eyebrows raised, and her mouth open in a small round shape, startled by her own thunder. ",
        "neg": ", closed eyes, calm expression, smile",
    },
    13: {  # 拗ね・不機嫌
        "tags": "starry sparkling cyan-blue eyes, pout, puffed cheeks, sulky, annoyed, furrowed brows, frown, looking to the side, ",
        "prose": "She is sulking and pouting, her cheeks slightly puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout, glancing to the side. ",
        "neg": ", smile, happy, blush, wide eyes, open mouth",
    },
    14: {  # 照れ・恋
        "tags": EYES_OPEN + "blush, deep blush, red cheeks, embarrassed, shy, in love, small bashful smile, looking to the side, averted gaze, ",
        "prose": "She is deeply embarrassed and lovestruck, her cheeks blushing bright pink, her gaze turned slightly to the side away from the viewer, with a small bashful happy smile. ",
        "neg": ", looking at viewer, angry, frown, calm expression",
    },
    15: {  # 目閉じ
        "tags": "closed eyes, serene expression, gentle smile, sleepy, content, ",
        "prose": "Her eyes are gently closed, with a calm serene and content expression and a soft peaceful smile, as if satisfied and a little sleepy. ",
        "neg": ", open eyes, looking at viewer, frown, angry",
    },
}

def seeds_for(surface):
    return [BASE_SEED, 92000 + surface * 10 + 1, 92000 + surface * 10 + 2]

def run(surface, seed):
    cfg = EXPRS[surface]
    positive = BASE_TAGS + cfg["tags"] + SKIN_DRESS + BODY_PROSE + cfg["prose"] + BG_PROSE
    negative = NEG_BASE + cfg["neg"]
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":positive}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":negative}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"furfur_expr{surface}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("EXPR", surface, "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("EXPR", surface, "SEED", seed, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("EXPR", surface, "SEED", seed, "TIMEOUT", flush=True)
    return 3

rc = 0
for e in sorted(EXPRS):
    for s in seeds_for(e):
        r = run(e, s)
        if r != 0:
            rc = r
            print("failed", e, s, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
