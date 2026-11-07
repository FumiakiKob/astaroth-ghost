import json, urllib.request, time, sys

# 第3シェル（メイド服）表情差分生成。
# 土台はユーザー採用候補そのもの：アスタロト=M1（seed 20261121、クラシック
# メイド黒×白）、フルフル=M3（seed 777701、クラシックメイド黒×白）。
# 手順は gen_night_expr.py 踏襲：土台と同シード・同衣装指定で表情指定だけを
# 差し替える。基準は surface0〜5 / 10〜15 の表情対応：
#   アスタロト 1=笑顔 2=驚き 3=呆れ 4=照れ 5=目閉じ
#   フルフル 11=満面の笑顔 12=驚き 13=拗ね 14=照れ・恋 15=目閉じ
# フルフルには gen_maid_candidates.py／gen_v224.py で実績のある頭身指示
# （PROP_*）を全ジョブに入れる。
# usage: gen_maid_expr.py [label ...]  （無指定で全件。WSL 上で実行する）

# ---------------- アスタロト M1 ----------------
ASTA_BASE = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, "
    "round pupils, (pale skin:0.3), gold pendant, halo, "
)
ASTA_OUTFIT = (
    "maid, classic maid outfit, black maid dress, white frill apron, lace headdress, "
    "maid headdress, white lace trim, long sleeves, puffy shoulders, knee-length dress, "
    "white stockings, black mary janes, "
)
ASTA_STANDING = (
    "A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
    "her whole body from the top of her halo to the tips of her feet fully visible inside the frame "
    "with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
    "hands empty. "
)
ASTA_BG = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair and clothes clearly separated from the green background."
)
ASTA_TAIL = (
    " She wears a classic maid outfit, a black maid dress with a white frilled apron over it and a "
    "white lace headdress on her head, tasteful and modest, the skirt of the dress falling to around "
    "her knees."
)
ASTA_NEG = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
    "black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, "
    "underwear, bra, panties, lingerie set, excessively revealing, see-through body, "
    "nightgown, negligee, pajamas, naked apron"
)
ASTA_EYES = "golden amber eyes, round pupils, "
ASTA_EXPRS = {
    1: {  # 笑顔
        "tags": ASTA_EYES + "gentle smile, warm smile, happy, ",
        "prose": "She has a gentle warm smile, her golden eyes open and looking softly at the viewer, a kind and happy expression. ",
        "neg": ", frown, angry, closed eyes, sad",
    },
    2: {  # 驚き
        "tags": "golden amber eyes, wide eyes, surprised, raised eyebrows, open mouth, :o, ",
        "prose": "She looks genuinely surprised, her eyes wide open, her eyebrows raised, and her mouth slightly open in a small round shape. ",
        "neg": ", closed eyes, calm expression, smile",
    },
    3: {  # 呆れ・不機嫌
        "tags": "golden amber eyes, half-closed eyes, narrowed eyes, unimpressed, annoyed, furrowed brows, frown, flat mouth, ",
        "prose": "She looks unimpressed and exasperated, with half-closed narrowed eyes, slightly furrowed eyebrows and a flat displeased mouth, as if quietly sighing at something foolish. ",
        "neg": ", smile, happy, blush, wide eyes",
    },
    4: {  # 照れ
        "tags": ASTA_EYES + "blush, pink cheeks, embarrassed, shy, looking to the side, averted gaze, small bashful smile, ",
        "prose": "She is embarrassed and shy, her cheeks blushing pink, her gaze turned slightly to the side away from the viewer, with a small bashful smile. ",
        "neg": ", looking at viewer, angry, frown",
    },
    5: {  # 目閉じ
        "tags": "closed eyes, serene expression, gentle smile, ",
        "prose": "Her eyes are gently closed, with a calm serene expression and a soft peaceful smile. ",
        "neg": ", open eyes, looking at viewer, frown, angry",
    },
}

# ---------------- フルフル M3 ----------------
FUR_BASE = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, "
    "round pupils, pinkish skin, blush, "
    "white feather wings, two small white feather wings on her back, "
)
PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"
FUR_OUTFIT = (
    "maid, black maid dress, maid outfit, white frill apron, lace headdress, maid headdress, "
    "white lace trim, puffy short sleeves, knee-length dress, white stockings, black mary janes, "
)
FUR_HEAD = (
    "A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
    "her whole body from the top of her head to the tips of her feet fully visible inside the frame "
    "with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
    "hands empty. "
)
FUR_WEAR = (
    "She wears a classic black and white maid outfit, a black maid dress with a white frilled "
    "apron over it and a white lace headdress on her head, cheerful and modest, its skirt ending "
    "around her knees. "
)
FUR_WINGS = (
    "Two small white feather wings spread slightly behind her back, modest in size, fully visible "
    "inside the frame and not too large. "
)
FUR_BG = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background."
)
FUR_NEG_BASE = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
    "halo, purple hair, black hair, dark hair, gold dress, long dress, "
    "deer, antlers, horns, tail, animal ears, huge wings, giant wings, "
    "underwear, bra, panties, lingerie set, excessively revealing"
)
FUR_NEG = FUR_NEG_BASE + ", pink dress, nightgown, negligee, pajamas" + PROP_NEG
FUR_EYES = "blue eyes, sparkling eyes, round pupils, "
FUR_EXPRS = {
    11: {  # 満面の笑顔
        "tags": FUR_EYES + "big smile, open mouth smile, :d, very happy, joyful, laughing, ",
        "prose": "She has a big joyful open-mouth smile, beaming happily at the viewer, full of energy and delight. ",
        "neg": ", frown, angry, closed eyes, sad, calm expression",
    },
    12: {  # 驚き
        "tags": "blue eyes, sparkling eyes, wide eyes, surprised, raised eyebrows, open mouth, :o, ",
        "prose": "She looks genuinely surprised, her eyes wide open, her eyebrows raised, and her mouth open in a small round shape, startled by her own thunder. ",
        "neg": ", closed eyes, calm expression, smile",
    },
    13: {  # 拗ね・不機嫌
        "tags": FUR_EYES + "pout, puffed cheeks, sulky, annoyed, furrowed brows, frown, looking to the side, ",
        "prose": "She is sulking and pouting, her cheeks slightly puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout, glancing to the side. ",
        "neg": ", smile, happy, blush, wide eyes, open mouth",
    },
    14: {  # 照れ・恋
        "tags": FUR_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, small bashful smile, looking to the side, averted gaze, ",
        "prose": "She is deeply embarrassed and lovestruck, her cheeks blushing bright pink, her gaze turned slightly to the side away from the viewer, with a small bashful happy smile. ",
        "neg": ", looking at viewer, angry, frown, calm expression",
    },
    15: {  # 目閉じ
        "tags": "closed eyes, serene expression, gentle smile, sleepy, content, ",
        "prose": "Her eyes are gently closed, with a calm serene and content expression and a soft peaceful smile, as if satisfied and a little sleepy. ",
        "neg": ", open eyes, looking at viewer, frown, angry",
    },
}

JOBS = []
for n, e in ASTA_EXPRS.items():
    pos = ASTA_BASE + ASTA_OUTFIT + e["tags"] + ASTA_STANDING + e["prose"] + ASTA_BG + ASTA_TAIL
    JOBS.append((f"MA{n}", 20261121, pos, ASTA_NEG + e["neg"]))
for n, e in FUR_EXPRS.items():
    pos = FUR_BASE + PROP_TAGS + FUR_OUTFIT + e["tags"] + FUR_HEAD + FUR_WEAR + PROP_PROSE + FUR_WINGS + e["prose"] + FUR_BG
    JOBS.append((f"MF{n}", 777701, pos, FUR_NEG + e["neg"]))

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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"maid_expr_{label}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("JOB", label, "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("JOB", label, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("JOB", label, "TIMEOUT", flush=True)
    return 3

only = sys.argv[1:] if len(sys.argv) > 1 else None
rc = 0
for label, seed, pos, neg in JOBS:
    if only and label not in only:
        continue
    r = run(label, seed, pos, neg)
    if r != 0:
        rc = r
        print("job failed", label, r, flush=True)
print("DONE rc=", rc)
sys.exit(rc)
