import json, urllib.request, time, sys

# フルフル ポーズ差分の表情違い（56〜59）生成。gen_pose_expr.py（アスタロト）を踏襲：
# 土台・シード・ポーズ指定は採用候補と同一にし、表情指定だけを差し替える。
#   56 = pose16(seed 16101) 照れ・恋
#   57 = pose17(seed 17102) 目閉じ（至福）
#   58 = pose18(seed 1031)  驚き（振り向き）
#   59 = pose19(seed 1031)  笑顔（満面）
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
SYMBOL_NEG = ", floating symbols, steam puffs, emphasis lines, motion lines, sparkles"

RUNS = [
    (
        56, 16101,
        BASE_TAGS
        + "leaning forward, bending forward, reaching out, arms reaching toward viewer, open hands, "
        + EYES_OPEN + "blush, deep blush, red cheeks, embarrassed, shy, in love, bashful smile, "
        + SKIN_DRESS
        + FRAME + "leaning forward toward the viewer with her upper body tilted in eagerly, both arms stretched out toward the viewer with open palms as if reaching out to grab or hug the viewer, an eager pushy posture full of energy. " + IDENTITY
        + "She is deeply embarrassed and lovestruck even as she leans in close, her cheeks blushing bright pink, with a small bashful happy smile, her gaze eager but shy. "
        + BG_PROSE,
        NEG_BASE + HAND_NEG + ", standing straight, arms hanging at sides, calm expression, angry, frown, closed eyes",
    ),
    (
        57, 17102,
        BASE_TAGS
        + "arms spread wide, arms outstretched to the sides, joyful, closed eyes, blissful, content, gentle smile, satisfied, "
        + SKIN_DRESS
        + FRAME + "standing straight and facing the viewer with both arms spread wide open to her sides in delight, her two white feather wings also spread wide behind her shoulders, a joyful welcoming posture. " + IDENTITY
        + "Her eyes are gently closed in pure bliss, with a satisfied content smile, savoring the happy moment. "
        + BG_PROSE,
        NEG_BASE + ", arms hanging at sides, folded wings, open eyes, looking at viewer, frown",
    ),
    (
        58, 1031,
        BASE_TAGS
        + "from behind, back view, three-quarter back view, looking back, looking over shoulder, arms crossed, surprised, wide eyes, raised eyebrows, open mouth, :o, "
        + SKIN_DRESS
        + FRAME + "shown from a three-quarter back view with her body turned away from the viewer, her arms crossed over her chest, her head turned to look back over her shoulder at the viewer, her white feather wings visible from behind her shoulders. " + IDENTITY
        + "She looks genuinely surprised as she glances back over her shoulder, her starry sparkling cyan-blue eyes wide open, her eyebrows raised, her mouth open in a small round shape, caught off guard. "
        + BG_PROSE,
        NEG_BASE + SYMBOL_NEG + ", body facing viewer, full front view, closed eyes, calm expression, smile, pout, puffed cheeks",
    ),
    (
        59, 1031,
        BASE_TAGS
        + "hands clasped, own hands together, hands clasped in front of chest, begging, upward gaze, looking up, "
        + EYES_OPEN + "big smile, open mouth smile, :d, very happy, joyful, "
        + SKIN_DRESS
        + FRAME + "standing straight and facing the viewer, both hands clasped together tightly in front of her chest in a begging gesture, leaning very slightly forward, not holding anything. " + IDENTITY
        + "She has a big joyful open-mouth smile, beaming happily up at the viewer as she begs, full of energy and delight, her starry eyes sparkling. "
        + BG_PROSE,
        NEG_BASE + ", arms hanging at sides, looking down, angry, frown, closed eyes, sad, small smile",
    ),
]

def run(surface, seed, positive, negative):
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
for (surf, seed, pos, neg) in RUNS:
    r = run(surf, seed, pos, neg)
    if r != 0:
        rc = r
        print("failed", surf, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
