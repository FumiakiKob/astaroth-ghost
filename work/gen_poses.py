import json, urllib.request, time, sys

# gen_expr.py を踏襲。ポーズ指定（タグ＋文章）だけを差し替える。表情は原則ニュートラル。
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
CALM = "She has a calm gentle expression, her golden eyes looking softly at the viewer. "

POSES = {
    6: {  # 腕を下げて前で手を重ねる（正面・素直な立ち）
        "variants": {
            "main": {
                "tags": "standing, own hands together, hands clasped in front, ",
                "prose": FRAME + "standing straight and facing the viewer, her arms lowered in front of her body with both hands gently clasped together in front of her waist, a calm docile standing posture, not holding anything. " + DRESS_TAIL,
                "expr": CALM,
                "neg": "",
            },
        },
        "seeds": [(20261101, "main"), (96101, "main"), (96102, "main")],
    },
    7: {  # 胸の前で手を合わせ少し俯く（斜め横向き）
        "variants": {
            "main": {
                "tags": "three-quarter view, own hands together, hands clasped in front of chest, head bowed, worried expression, ",
                "prose": FRAME + "shown in a three-quarter view with her body turned slightly to the side, both hands clasped together in front of her chest, her head slightly bowed, not holding anything. " + DRESS_TAIL,
                "expr": "She has a gentle worried expression, her eyebrows slightly raised in concern, gazing quietly toward the viewer. ",
                "neg": "",
            },
        },
        "seeds": [(20261101, "main"), (97101, "main"), (97102, "main")],
    },
    8: {  # 本を持つ（A・C=片手持ち、B=抱える）
        "variants": {
            "onehand": {
                "tags": "holding book, book, old book, ",
                "prose": FRAME + "standing straight and facing the viewer, holding a thick old leather-bound book in one hand down at her side, her other arm relaxed and hanging naturally at her side. " + DRESS_TAIL,
                "expr": CALM,
                "neg": "",
                "neg_replace": True,
            },
            "hug": {
                "tags": "holding book, book, old book, ",
                "prose": FRAME + "standing straight and facing the viewer, hugging a thick old leather-bound book against her chest with both arms. " + DRESS_TAIL,
                "expr": CALM,
                "neg": "",
                "neg_replace": True,
            },
        },
        "seeds": [(20261101, "onehand"), (98101, "hug"), (98102, "onehand")],
    },
    9: {  # 腕組み
        "variants": {
            "main": {
                "tags": "arms crossed, crossed arms, looking down, confident, ",
                "prose": FRAME + "standing straight and facing the viewer, her arms firmly crossed over her chest, her chin slightly raised in a confident posture, not holding anything. " + DRESS_TAIL,
                "expr": "She looks slightly down at the viewer with a composed, mildly condescending, unimpressed expression. ",
                "neg": "",
            },
        },
        "seeds": [(20261101, "main"), (99101, "main"), (99102, "main")],
    },
}

def run(pose, seed, varkey):
    cfg = POSES[pose]["variants"][varkey]
    positive = BASE_TAGS + cfg["tags"] + EYES_OPEN + SKIN_DRESS + cfg["prose"] + cfg["expr"] + BG_PROSE
    negative = NEG_BASE
    if cfg.get("neg_replace"):
        negative = negative.replace("holding book, holding object, ", "")
    negative = negative + cfg["neg"]
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":positive}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":negative}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"astaroth_pose{pose}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("POSE", pose, "SEED", seed, "VAR", varkey, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("POSE", pose, "SEED", seed, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("POSE", pose, "SEED", seed, "TIMEOUT", flush=True)
    return 3

rc = 0
for p in sorted(POSES):
    for (s, v) in POSES[p]["seeds"]:
        r = run(p, s, v)
        if r != 0:
            rc = r
            print("failed", p, s, v, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
