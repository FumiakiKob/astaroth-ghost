import json, urllib.request, time, sys

# 座りポーズ（アスタロト20／フルフル21）の候補生成。
# キャラ固定仕様は gen_poses.py（アスタロト）／gen_furfur_poses.py（フルフル）
# をそのまま流用し、ポーズ指定だけを座りに差し替える。
# 椅子を描くため NEG から furniture／sitting を外す（座り専用の調整）。

# ---------------- アスタロト ----------------
A_BASE_TAGS = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "deep purple and violet hair, long hair, wavy hair, choppy bangs, "
)
A_EYES_OPEN = "golden amber eyes, round pupils, "
A_SKIN_DRESS = (
    "(pale skin:0.3), gold pendant, halo, "
    "black and gold off-shoulder dress, elegant long dress with gold trim, "
    "gold chain necklace with demon crest pendant, black heeled shoes, "
)
A_FRAME = (
    "A petite fallen angel girl in a full body shot, seated on a chair, "
    "the whole chair and her whole body from the top of her halo to the bottom of the chair "
    "fully visible inside the frame with margin around them, "
)
A_DRESS_TAIL = "She wears an elegant black and gold off-shoulder dress. "
BG_PROSE = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair, dress and chair clearly separated from the green background."
)
A_NEG = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "gradient background, multiple girls, holding book, holding object, standing, "
    "legs spread, crossed legs, ornate chair, throne, sofa, armchair"
)
A_CALM = "She has a calm gentle expression, her golden eyes looking softly at the viewer. "

# ---------------- フルフル ----------------
F_BASE_TAGS = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "white hair, twintails, hair just past shoulders, curled hair ends, "
    "small pink hair ties, long face-framing sidelocks, choppy bangs, "
)
F_EYES_OPEN = "starry sparkling cyan-blue eyes, star-shaped highlights in eyes, round pupils, "
F_SKIN_DRESS = (
    "pinkish skin, blush, "
    "pink sleeveless dress, white frilled shoulder straps, small white bow, "
    "white lace-up criss-cross ribbon on the front of the bodice, gathered waist, "
    "flared skirt with a thin white line near the hem, white frilled petticoat hem under the skirt, "
    "pink mary jane shoes with ankle straps, "
    "white feather wings, two large white feather wings behind her shoulders, "
)
F_FRAME = (
    "A petite fallen angel girl in a full body shot, seated on a chair, "
    "the whole chair and her whole body from the top of her head to the bottom of the chair "
    "fully visible inside the frame with margin around them, "
)
F_IDENTITY = (
    "She is always the same girl with the same face, the same starry sparkling "
    "cyan-blue eyes, the same white twintails with curled ends and pink hair ties, and the same "
    "outfit: a pink sleeveless dress with white frilled shoulder straps, a small white bow and a "
    "white lace-up criss-cross ribbon on the front of the bodice, and a white frilled petticoat "
    "hem under the flared skirt. Two large white feather wings behind her shoulders, "
    "fully visible inside the frame. "
)
F_NEG = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "gradient background, multiple girls, holding book, holding object, standing, "
    "halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
    "deer, antlers, horns, tail, animal ears, huge wings, giant wings, "
    "ornate chair, throne, sofa, armchair, cast shadow, ground shadow, drop shadow"
)
F_HAND_NEG = ", oversized hands, huge hands, big hands, disproportionate hands, long fingers"

JOBS = [
    {  # アスタロト20：椅子に腰掛け、膝を揃え、背筋を伸ばす
        "surface": 20, "prefix": "astaroth_sit20",
        "positive": (
            A_BASE_TAGS
            + "sitting, sitting on a chair, chair, legs together, knees together, upright posture, "
            + A_EYES_OPEN + A_SKIN_DRESS
            + A_FRAME
            + "sitting gracefully on a simple plain wooden chair, facing the viewer, her knees "
              "together and her back straight in an upright elegant posture, her hands resting "
              "gently on her lap, the skirt of her long dress spreading softly over her knees, "
              "her feet resting in front of the chair, absolutely no shadow cast on the ground beneath or around her. "
            + A_DRESS_TAIL + A_CALM + BG_PROSE
        ),
        "negative": A_NEG,
        "seeds": [201103, 201104, 201105],
    },
    {  # フルフル21：座って足をぶらつかせる
        "surface": 21, "prefix": "furfur_sit21",
        "positive": (
            F_BASE_TAGS
            + "sitting, sitting on a chair, chair, legs dangling, swinging legs, relaxed, happy, "
            + F_EYES_OPEN + F_SKIN_DRESS
            + F_FRAME
            + "sitting on a simple plain wooden chair that is a little tall for her, facing the "
              "viewer, her short legs dangling off the front edge of the seat and swinging "
              "playfully in the air, her feet not touching the floor, her hands resting on the "
              "seat beside her hips, a relaxed carefree posture. "
            + F_IDENTITY
            + "She has a cheerful relaxed expression with a happy open-mouth smile, enjoying "
              "herself as she swings her legs. "
            + BG_PROSE
        ),
        "negative": F_NEG + F_HAND_NEG + ", feet on floor, standing",
        "seeds": [],
    },
]

def run(job, seed):
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":job["positive"]}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":job["negative"]}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"{job['prefix']}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("SURF", job["surface"], "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            outs=h[pid].get("outputs",{})
            print("SURF", job["surface"], "SEED", seed, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("SURF", job["surface"], "SEED", seed, "TIMEOUT", flush=True)
    return 3

rc = 0
for j in JOBS:
    for s in j["seeds"]:
        r = run(j, s)
        if r != 0:
            rc = r
            print("failed", j["surface"], s, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
