import json, urllib.request, time, sys

# v2.24 生成スクリプト。
# 夜シェル フルフル基本＋表情 10〜15 の頭身是正（v2.23 で再キーイングのみだった残りの是正）。
# 流儀は gen_v223.py の furfur_master_base と同一：土台シード（夜フルフル=121601）＋
# 表情指定のみ差し替え＋頭身指示（PROP_*）を全ジョブに入れる。
# 衣装は N5（黒の短いネグリジェ＋白レース）で、夜ポーズ面（NF16-19/56-59/21）と同一系統。
# usage: gen_v224.py [label ...]  （無指定で全件。WSL 上で実行する）

PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, the same height as another girl of similar stature standing beside her, "
              "elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"

BG = ("Behind her is a completely plain solid bright green background, a single flat uniform green "
      "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
      "no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background.")
FRAME = ("A petite fallen angel girl in a full body shot, her whole body from the top of her head to the tips "
         "of her feet fully visible inside the frame with margin around her, ")

F_BASE = ("masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
          "white hair, twintails, hair just past shoulders, curled hair ends, "
          "small pink hair ties, long face-framing sidelocks, choppy bangs, ")
F_EYES = "starry sparkling cyan-blue eyes, star-shaped highlights in eyes, round pupils, "
F_NEG_TAIL = (", halo, purple hair, black hair, dark hair, deer, antlers, horns, tail, animal ears, huge wings, giant wings")

# 夜 N5（gen_v223.py の N_SKIN / N_WEAR / N_NEG と同一）
N_SKIN = ("pinkish skin, blush, short black babydoll negligee, black silk nightgown, white lace trim, frills, "
          "nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet, "
          "white feather wings, two small white feather wings on her back, ")
N_WEAR = ("She wears a cute short black babydoll negligee with white lace trim and frills, tasteful and "
          "modest, its skirt ending above her knees. Two small white feather wings spread slightly behind "
          "her back, modest in size, fully visible inside the frame and not too large. ")
N_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
         "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
         "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
         "gold dress, long dress, underwear, bra, panties, lingerie set, excessively revealing, "
         "pajamas, long pants, trousers, pink negligee, pink nightgown, pink dress" + F_NEG_TAIL)

# 基本＋表情（10=通常、11=満面の笑顔、12=驚き、13=拗ね、14=照れ・恋、15=目閉じ）
# gen_v223.py の M_EXPRS と同一の表情対応。
N_EXPRS = {
    10: (F_EYES + "cheerful smile, gentle smile, happy, ",
         "She has a cheerful gentle smile, her sparkling blue eyes open and looking at the viewer, bright and energetic. ",
         ", frown, angry, closed eyes, sad"),
    11: (F_EYES + "big smile, open mouth smile, :d, very happy, joyful, laughing, ",
         "She has a big joyful open-mouth smile, beaming happily at the viewer, full of energy and delight. ",
         ", frown, angry, closed eyes, sad, calm expression"),
    12: ("blue eyes, sparkling eyes, wide eyes, surprised, raised eyebrows, open mouth, :o, ",
         "She looks genuinely surprised, her eyes wide open, her eyebrows raised, and her mouth open in a small round shape, startled by her own thunder. ",
         ", closed eyes, calm expression, smile"),
    13: (F_EYES + "pout, puffed cheeks, sulky, annoyed, furrowed brows, frown, looking to the side, ",
         "She is sulking and pouting, her cheeks slightly puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout, glancing to the side. ",
         ", smile, happy, blush, wide eyes, open mouth"),
    14: (F_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, small bashful smile, looking to the side, averted gaze, ",
         "She is deeply embarrassed and lovestruck, her cheeks blushing bright pink, her gaze turned slightly to the side away from the viewer, with a small bashful happy smile. ",
         ", looking at viewer, angry, frown, calm expression"),
    15: ("closed eyes, serene expression, gentle smile, sleepy, content, ",
         "Her eyes are gently closed, with a calm serene and content expression and a soft peaceful smile, as if satisfied and a little sleepy. ",
         ", open eyes, looking at viewer, frown, angry"),
}

JOBS = []  # (label, seed, positive, negative)

def furfur_night_base(surf):
    etags, eprose, eneg = N_EXPRS[surf]
    pos = (F_BASE + PROP_TAGS + etags + N_SKIN + FRAME
           + "standing straight and facing the viewer, arms relaxed and hanging naturally at her sides, not holding anything, hands empty. "
           + N_WEAR + PROP_PROSE + eprose + BG)
    return (f"NF{surf}", 121601, pos, N_NEG + eneg + PROP_NEG)

for s in (10, 11, 12, 13, 14, 15):
    JOBS.append(furfur_night_base(s))

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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"v224_{label}_seed{seed}"}}
    }
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid = resp["prompt_id"]
    print("JOB", label, "SEED", seed, "PID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st = h[pid].get("status", {})
            print("JOB", label, "STATUS", st.get("status_str"), flush=True)
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
        print("FAILED", label, r, flush=True)
print("DONE rc=", rc, flush=True)
sys.exit(rc)
