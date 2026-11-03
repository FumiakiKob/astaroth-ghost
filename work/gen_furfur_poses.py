import json, urllib.request, time, sys

# フルフル ポーズ差分（16〜19）の候補生成。gen_furfur_expr.py（表情差分）の
# キャラ固定仕様をそのまま使い、ポーズ指定（タグ＋文章）だけを差し替える。
# 表情はポーズごとに「素」の顔（16=興奮／17=喜び／18=拗ね／19=お願い）。
# 候補はポーズごとに3シード（基準シード1031＋別シード2）。
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
    "white feather wings, two large white feather wings behind her shoulders, "
)
FRAME = (
    "A petite fallen angel girl in a full body shot, "
    "her whole body from the top of her head to the tips of her shoes fully visible inside the frame "
    "with margin around her, "
)
IDENTITY = (
    "She is always the same girl with the same face, the same starry sparkling "
    "cyan-blue eyes, the same white twintails with curled ends and pink hair ties, and the same "
    "outfit: a pink sleeveless dress with white frilled shoulder straps, a small white bow and a "
    "white lace-up criss-cross ribbon on the front of the bodice, and a white frilled petticoat "
    "hem under the flared skirt. Two large white feather wings behind her shoulders, "
    "fully visible inside the frame. "
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
HAND_NEG = ", oversized hands, huge hands, big hands, disproportionate hands, long fingers"

POSES = {
    16: {  # 身を乗り出す（素の顔＝興奮）
        "tags": "leaning forward, bending forward, reaching out, arms reaching toward viewer, open hands, excited, happy, open mouth smile, :d, " + EYES_OPEN,
        "prose": FRAME + "leaning forward toward the viewer with her upper body tilted in eagerly, both arms stretched out toward the viewer with open palms as if reaching out to grab or hug the viewer, an eager pushy posture full of energy. " + IDENTITY,
        "expr": "She has an eager excited expression, sparkling eyes and a big happy open-mouth smile, thrilled to get closer. ",
        "neg": HAND_NEG + ", standing straight, arms hanging at sides, calm expression, frown",
        "seeds": [1031, 16101, 16102],
    },
    17: {  # 両手を広げて喜ぶ（素の顔＝喜び）
        "tags": "arms spread wide, arms outstretched to the sides, joyful, happy, open mouth smile, :d, " + EYES_OPEN,
        "prose": FRAME + "standing straight and facing the viewer with both arms spread wide open to her sides in delight, her two white feather wings also spread wide behind her shoulders, a joyful welcoming posture. " + IDENTITY,
        "expr": "She has a bright joyful expression with a big happy open-mouth smile, beaming with delight. ",
        "neg": ", arms hanging at sides, folded wings, closed eyes, calm expression, frown",
        "seeds": [1031, 17101, 17102],
    },
    18: {  # 拗ねてそっぽ（素の顔＝拗ね）
        "tags": "from behind, back view, three-quarter back view, looking back, looking over shoulder, arms crossed, pout, puffed cheeks, sulky, annoyed, furrowed brows, ",
        "prose": FRAME + "shown from a three-quarter back view with her body turned away from the viewer in a sulk, her arms crossed over her chest, her head turned to look back over her shoulder at the viewer, her white feather wings visible from behind her shoulders. " + IDENTITY,
        "expr": "She is sulking and pouting, her cheeks puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout as she glares back over her shoulder with starry sparkling cyan-blue eyes. ",
        "neg": ", body facing viewer, full front view, smile, happy, joyful, open mouth smile",
        "seeds": [1031, 18101, 18102],
    },
    19: {  # 両手を胸の前で合わせてお願い（素の顔＝お願い・上目遣い）
        "tags": "hands clasped, own hands together, hands clasped in front of chest, begging, pleading, upward gaze, looking up, " + EYES_OPEN,
        "prose": FRAME + "standing straight and facing the viewer, both hands clasped together tightly in front of her chest in a begging gesture, leaning very slightly forward, not holding anything. " + IDENTITY,
        "expr": "She looks up at the viewer with a pleading upward gaze, her starry eyes sparkling hopefully, her mouth in a small hopeful smile, earnestly begging for a favor. ",
        "neg": ", arms hanging at sides, looking down, angry, frown, closed eyes",
        "seeds": [1031, 19101, 19102],
    },
}

def run(surface, seed):
    cfg = POSES[surface]
    positive = BASE_TAGS + cfg["tags"] + SKIN_DRESS + cfg["prose"] + cfg["expr"] + BG_PROSE
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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"furfur_pose{surface}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("POSE", surface, "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("POSE", surface, "SEED", seed, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("POSE", surface, "SEED", seed, "TIMEOUT", flush=True)
    return 3

rc = 0
for p in sorted(POSES):
    for s in POSES[p]["seeds"]:
        r = run(p, s)
        if r != 0:
            rc = r
            print("failed", p, s, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
